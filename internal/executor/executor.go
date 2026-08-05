package executor

import (
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/skupperproject/sketcher/internal/demo"
	"github.com/skupperproject/sketcher/internal/kubernetes"
	"github.com/skupperproject/sketcher/internal/model"
	"github.com/skupperproject/sketcher/internal/utils"
)

// Export NewModel for use by cli package
var NewModel = model.NewModel

// RunSteps executes all steps from a skewer.yaml file
func RunSteps(yamlFile string, kubeconfigs []string, workDir string, debug, quiet bool) error {
	utils.Info("Running steps from %s", yamlFile)

	// Setup signal handler and cleanup
	SetupSignalHandler()
	defer CleanupBackgroundProcesses()

	// Check environment
	if err := kubernetes.CheckEnvironment(); err != nil {
		return err
	}

	// Load model
	m, err := model.NewModel(yamlFile, kubeconfigs)
	if err != nil {
		return err
	}

	if err := m.Check(); err != nil {
		return err
	}

	// Create work directory
	if workDir == "" {
		// Use /tmp directly to avoid macOS temp paths with special characters
		// that fail skupper's token file path validation (regex: ^[A-Za-z0-9./~-]+$)
		baseDir := "/tmp"
		utils.Debug("Creating temporary work directory in %s", baseDir)
		tempDir, err := os.MkdirTemp(baseDir, "sketcher-")
		if err != nil {
			return fmt.Errorf("failed to create work directory: %w", err)
		}
		workDir = tempDir
		utils.Info("Using work directory: %s", workDir)
	} else {
		utils.Debug("Using specified work directory: %s", workDir)
		if err := os.MkdirAll(workDir, 0755); err != nil {
			return err
		}
		utils.Debug("Work directory created: %s", workDir)
	}

	// Run all steps except cleaning_up
	for _, step := range m.Steps {
		if step.Name == "cleaning_up" {
			continue
		}

		if err := runStep(m, step, workDir, true, quiet); err != nil {
			if debug {
				printDebugOutput(m)
			}
			return err
		}
	}

	// Demo mode support
	if os.Getenv("SKETCHER_DEMO") != "" {
		// Save demo context
		if err := demo.SaveDemoContext(m, workDir); err != nil {
			return fmt.Errorf("failed to save demo context: %w", err)
		}

		// Pause and display demo information
		if err := demo.PauseForDemo(m, quiet); err != nil {
			return fmt.Errorf("failed during demo pause: %w", err)
		}
	}

	// Always run cleaning_up if it exists
	for _, step := range m.Steps {
		if step.Name == "cleaning_up" {
			runStep(m, step, workDir, false, true)
			break
		}
	}

	return nil
}

func runStep(m *model.Model, step *model.Step, workDir string, check, quiet bool) error {
	if len(step.Commands) == 0 {
		return nil
	}

	// Check if all commands are readme-only
	allReadme := true
	for _, commands := range step.Commands {
		for _, cmd := range commands {
			if cmd.Apply != "readme" {
				allReadme = false
				break
			}
		}
		if !allReadme {
			break
		}
	}

	if allReadme {
		return nil
	}

	// Log step
	if !quiet {
		utils.Cprint(fmt.Sprintf("→ %s", stepString(step)), "cyan")
	}

	for _, site := range m.Sites {
		commands, ok := step.Commands[site.Name]
		if !ok {
			continue
		}

		// Set environment variables for site
		err := site.WithEnv(func() error {
			// Set kubectl namespace for kubernetes sites
			if site.Platform == "kubernetes" {
				cmd := exec.Command("kubectl", "config", "set-context", "--current", "--namespace", site.Namespace)
				cmd.Stdout = nil
				cmd.Stderr = nil
				cmd.Run()
			}

			// Execute commands
			for _, command := range commands {
				if command.Apply == "readme" {
					continue
				}

				// Execute await operations
				if command.AwaitResource != "" {
					utils.Debug("Awaiting resource: %s", command.AwaitResource)
					if err := kubernetes.AwaitResource(command.AwaitResource, 300, quiet); err != nil {
						return err
					}
				}

				if command.AwaitIngress != "" {
					utils.Debug("Awaiting ingress: %s", command.AwaitIngress)
					if _, err := kubernetes.AwaitIngress(command.AwaitIngress, 300, quiet); err != nil {
						return err
					}
				}

				if len(command.AwaitHTTPOK) > 0 {
					utils.Debug("Awaiting HTTP OK")
					// Implementation would be in kubernetes package
				}

				if command.AwaitConsoleOK {
					utils.Debug("Awaiting console OK")
					if err := kubernetes.AwaitConsoleOK(300, quiet); err != nil {
						return err
					}
				}

				if command.AwaitPort > 0 {
					utils.Debug("Awaiting port: %d", command.AwaitPort)
					if err := utils.AwaitPort(command.AwaitPort, "localhost", 60); err != nil {
						return err
					}
				}

				// Execute shell command
				if command.Run != "" {
					cmdStr := strings.ReplaceAll(command.Run, "~", workDir)

					// Auto-inject platform flag for skupper commands on non-kubernetes platforms
					if site.Platform != "kubernetes" && strings.Contains(cmdStr, "skupper ") {
						// Only inject if -p/--platform is not already present
						if !strings.Contains(cmdStr, " -p ") && !strings.Contains(cmdStr, " --platform") {
							// Inject -p flag before -n flag or at the end
							if strings.Contains(cmdStr, " -n ") {
								cmdStr = strings.Replace(cmdStr, " -n ", fmt.Sprintf(" -p %s -n ", site.Platform), 1)
							} else {
								// Append at the end (before any trailing &)
								cmdStr = strings.TrimSpace(cmdStr)
								if strings.HasSuffix(cmdStr, "&") {
									cmdStr = strings.TrimSuffix(cmdStr, "&")
									cmdStr = strings.TrimSpace(cmdStr) + fmt.Sprintf(" -p %s &", site.Platform)
								} else {
									cmdStr = cmdStr + fmt.Sprintf(" -p %s", site.Platform)
								}
							}
						}
					}

					// Wrap localhost curl commands with retry logic
					if strings.Contains(cmdStr, "curl") && strings.Contains(cmdStr, "localhost") && strings.Contains(cmdStr, "http://") {
						if !strings.Contains(cmdStr, "--retry") {
							cmdStr = strings.ReplaceAll(cmdStr, "curl ", "curl --retry 20 --retry-delay 3 --retry-all-errors --max-time 15 ")
						}
					}

					// Check if this is a background command (ends with &)
					isBackground := strings.HasSuffix(strings.TrimSpace(cmdStr), "&")

					var err error
					if isBackground {
						// Remove the & and run as tracked background process
						cmdStr = strings.TrimSuffix(strings.TrimSpace(cmdStr), "&")
						err = RunBackgroundCommand(cmdStr)
					} else {
						// Run normally
						cmd := exec.Command("sh", "-c", cmdStr)
						cmd.Stdout = os.Stdout
						cmd.Stderr = os.Stderr
						err = cmd.Run()
					}

					if command.ExpectFailure {
						if err == nil {
							return fmt.Errorf("a command expected to fail did not fail")
						}
						continue
					}

					if check && err != nil {
						return fmt.Errorf("command failed in %s: %v", stepString(step), err)
					}
				}
			}

			return nil
		})

		if err != nil {
			return err
		}
	}

	if !quiet {
		utils.Cprint(fmt.Sprintf("✓ %s", stepString(step)), "green")
	}

	return nil
}

func printDebugOutput(m *model.Model) {
	fmt.Fprintf(os.Stderr, "\n%s\n", strings.Repeat("=", 80))
	utils.Cprint("DEBUG OUTPUT", "yellow")
	fmt.Fprintf(os.Stderr, "%s\n", strings.Repeat("=", 80))

	for _, site := range m.Sites {
		utils.Cprint(fmt.Sprintf("\n--- %s (%s) ---\n", site.Title, site.Name), "cyan")

		site.WithEnv(func() error {
			if site.Platform == "kubernetes" {
				cmd := exec.Command("kubectl", "config", "set-context", "--current", "--namespace", site.Namespace)
				cmd.Run()

				fmt.Fprintln(os.Stderr, "kubectl get all:")
				cmd = exec.Command("kubectl", "get", "all")
				cmd.Stdout = os.Stderr
				cmd.Stderr = os.Stderr
				cmd.Run()
				fmt.Fprintln(os.Stderr)
			}

			fmt.Fprintln(os.Stderr, "skupper status:")
			cmd := exec.Command("skupper", "status")
			cmd.Stdout = os.Stderr
			cmd.Stderr = os.Stderr
			cmd.Run()
			fmt.Fprintln(os.Stderr)

			return nil
		})
	}

	fmt.Fprintf(os.Stderr, "%s\n", strings.Repeat("=", 80))
}

func stepString(step *model.Step) string {
	if step.Numbered {
		return fmt.Sprintf("step %d '%s'", step.Number, step.Title)
	}
	return fmt.Sprintf("'%s'", step.Title)
}
