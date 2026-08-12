package cli

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/skupperproject/sketcher/internal/demo"
	"github.com/skupperproject/sketcher/internal/executor"
	"github.com/skupperproject/sketcher/internal/kind"
	"github.com/skupperproject/sketcher/internal/logger"
	"github.com/skupperproject/sketcher/internal/minikube"
	"github.com/skupperproject/sketcher/internal/utils"
)

// Execute runs the CLI with the given version
func Execute(version string) error {
	if len(os.Args) < 2 {
		printHelp()
		return nil
	}

	fmt.Printf("Sketcher %s\n", version)

	command := os.Args[1]

	switch command {
	case "run":
		return executeRun()
	case "demo":
		return executeDemo()
	case "demo-extend":
		return executeDemoExtend()
	case "test":
		return executeTest()
	case "clean":
		return executeClean()
	case "view-log":
		return executeViewLog()
	default:
		return fmt.Errorf("unknown command: %s", command)
	}
}

func executeRun() error {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	debug := fs.Bool("debug", false, "Show debug output on failure")
	verbose := fs.Bool("verbose", false, "Enable verbose debug output")
	quiet := fs.Bool("quiet", false, "Suppress progress messages")
	workDir := fs.String("work-dir", "", "Working directory (default: temp dir)")
	fs.Parse(os.Args[2:])

	configureLogging(*verbose, *quiet)

	yamlFile := "skewer.yaml"
	var kubeconfigs []string

	if fs.NArg() > 0 {
		yamlFile = fs.Arg(0)
		kubeconfigs = fs.Args()[1:]
	}

	return executor.RunSteps(yamlFile, kubeconfigs, *workDir, *debug, *quiet)
}

func executeDemo() error {
	fs := flag.NewFlagSet("demo", flag.ExitOnError)
	debug := fs.Bool("debug", false, "Show debug output on failure")
	verbose := fs.Bool("verbose", false, "Enable verbose debug output")
	quiet := fs.Bool("quiet", false, "Suppress progress messages")
	useKind := fs.Bool("kind", false, "Use Kind instead of Minikube")
	useKindLB := fs.Bool("kind-lb", false, "Use Kind with MetalLB for LoadBalancer ingress")
	fs.Parse(os.Args[2:])

	configureLogging(*verbose, *quiet)

	os.Setenv("SKETCHER_DEMO", "1")

	yamlFile := "skewer.yaml"
	var kubeconfigs []string

	if fs.NArg() > 0 {
		yamlFile = fs.Arg(0)
		kubeconfigs = fs.Args()[1:]
	}

	// Check if any sites require Kubernetes
	needsK8s, err := checkNeedsKubernetes(yamlFile)
	if err != nil {
		return err
	}

	if len(kubeconfigs) == 0 && needsK8s {
		if *useKind || *useKindLB {
			return runWithKind(yamlFile, *debug, *quiet, *useKindLB)
		}
		return runWithMinikube(yamlFile, *debug, *quiet)
	}

	return executor.RunSteps(yamlFile, kubeconfigs, "", *debug, *quiet)
}

func executeDemoExtend() error {
	fs := flag.NewFlagSet("demo-extend", flag.ExitOnError)
	debug := fs.Bool("debug", false, "Show debug output on failure")
	verbose := fs.Bool("verbose", false, "Enable verbose debug output")
	quiet := fs.Bool("quiet", false, "Suppress progress messages")
	fs.Parse(os.Args[2:])

	configureLogging(*verbose, *quiet)

	if fs.NArg() < 1 {
		return fmt.Errorf("missing extend file")
	}

	extendFile := fs.Arg(0)

	// Load demo context
	context, err := demo.LoadDemoContext("")
	if err != nil {
		return err
	}

	if err := demo.ValidateDemoContext(context); err != nil {
		return err
	}

	// Create extended model
	model, err := demo.CreateExtendedModel(context, extendFile)
	if err != nil {
		return err
	}

	return executor.RunSteps(model.YAMLFile, nil, context.WorkDir, *debug, *quiet)
}

func executeTest() error {
	fs := flag.NewFlagSet("test", flag.ExitOnError)
	debug := fs.Bool("debug", false, "Show debug output on failure")
	verbose := fs.Bool("verbose", false, "Enable verbose debug output")
	quiet := fs.Bool("quiet", false, "Suppress progress messages")
	useKind := fs.Bool("kind", false, "Use Kind instead of Minikube")
	useKindLB := fs.Bool("kind-lb", false, "Use Kind with MetalLB for LoadBalancer ingress")
	noExtensions := fs.Bool("no-extensions", false, "Skip running extension files (skewer-*.yaml)")
	fs.Parse(os.Args[2:])

	configureLogging(*verbose, *quiet)

	os.Setenv("SKETCHER_TEST", "1")

	yamlFile := "skewer.yaml"
	if fs.NArg() > 0 {
		yamlFile = fs.Arg(0)
	}

	// Check if any sites require Kubernetes
	needsK8s, err := checkNeedsKubernetes(yamlFile)
	if err != nil {
		return err
	}

	if needsK8s {
		if *useKind || *useKindLB {
			return testWithKind(yamlFile, *debug, *quiet, *noExtensions, *useKindLB)
		}
		return testWithMinikube(yamlFile, *debug, *quiet, *noExtensions)
	}

	return testWithoutCluster(yamlFile, *debug, *quiet, *noExtensions)
}

func executeClean() error {
	// Remove __pycache__ directories (not needed for Go)
	// Remove .demo-context.json files
	matches, err := filepath.Glob("**/.demo-context.json")
	if err != nil {
		return err
	}

	for _, match := range matches {
		if err := os.Remove(match); err != nil {
			utils.Warn("Failed to remove %s: %v", match, err)
		} else {
			utils.Info("Removed %s", match)
		}
	}

	utils.Cprint("Clean complete", "green")
	return nil
}

func executeViewLog() error {
	if len(os.Args) < 3 {
		return fmt.Errorf("usage: sketcher view-log <log-file>")
	}

	logFile := os.Args[2]
	return logger.ViewLog(logFile)
}

func printHelp() {
	fmt.Println("Usage: sketcher <command> [options]")
	fmt.Println()
	fmt.Println("Execution commands (use 'skewer' for YAML processing):")
	fmt.Println("  run          Run steps from resolved skewer.yaml")
	fmt.Println("  demo         Run steps and pause for demo")
	fmt.Println("  demo-extend  Extend an active demo with additional steps")
	fmt.Println("  test         Generate README (via skewer), run main steps, and run all extension files")
	fmt.Println("  clean        Remove generated files (.demo-context.json)")
	fmt.Println("  view-log     View a log file in human-readable format")
}

func configureLogging(verbose, quiet bool) {
	if verbose {
		utils.SetLogLevel(utils.LogLevelDebug)
	} else if quiet {
		utils.SetLogLevel(utils.LogLevelWarn)
	} else {
		utils.SetLogLevel(utils.LogLevelInfo)
	}
}

func checkNeedsKubernetes(yamlFile string) (bool, error) {
	model, err := executor.NewModel(yamlFile, nil)
	if err != nil {
		return false, err
	}

	for _, site := range model.Sites {
		if site.Platform == "kubernetes" {
			return true, nil
		}
	}

	return false, nil
}

func runWithKind(yamlFile string, debug, quiet, useMetalLB bool) error {
	k, err := kind.New(yamlFile, useMetalLB)
	if err != nil {
		return err
	}
	defer k.Cleanup(debug)

	// Clean work directory if there's a stale or different demo
	demo.CleanWorkDirIfNeeded(k.WorkDir, yamlFile)

	if err := k.Setup(); err != nil {
		return err
	}

	return executor.RunSteps(yamlFile, k.Kubeconfigs, k.WorkDir, debug, quiet)
}

func runWithMinikube(yamlFile string, debug, quiet bool) error {
	mk, err := minikube.New(yamlFile)
	if err != nil {
		return err
	}
	defer mk.Cleanup(debug)

	// Clean work directory if there's a stale or different demo
	demo.CleanWorkDirIfNeeded(mk.WorkDir, yamlFile)

	if err := mk.Setup(); err != nil {
		return err
	}

	return executor.RunSteps(yamlFile, mk.Kubeconfigs, mk.WorkDir, debug, quiet)
}

func testWithKind(yamlFile string, debug, quiet, noExtensions, useMetalLB bool) error {
	k, err := kind.New(yamlFile, useMetalLB)
	if err != nil {
		return err
	}
	defer k.Cleanup(debug)

	if err := k.Setup(); err != nil {
		return err
	}

	return runTest(yamlFile, k.Kubeconfigs, k.WorkDir, debug, quiet, noExtensions)
}

func testWithMinikube(yamlFile string, debug, quiet, noExtensions bool) error {
	mk, err := minikube.New(yamlFile)
	if err != nil {
		return err
	}
	defer mk.Cleanup(debug)

	if err := mk.Setup(); err != nil {
		return err
	}

	return runTest(yamlFile, mk.Kubeconfigs, mk.WorkDir, debug, quiet, noExtensions)
}

func testWithoutCluster(yamlFile string, debug, quiet, noExtensions bool) error {
	// Use /tmp directly to avoid macOS temp paths with special characters
	workDir := "/tmp/sketcher-"
	return runTest(yamlFile, nil, workDir, debug, quiet, noExtensions)
}

func runTest(yamlFile string, kubeconfigs []string, workDir string, debug, quiet, noExtensions bool) error {
	// Check for skewer availability
	if _, err := exec.LookPath("skewer"); err != nil {
		return fmt.Errorf("test command requires 'skewer' to be installed (pip install sketcher)")
	}

	// Generate README using Python skewer
	utils.Info("Generating README...")
	cmd := exec.Command("skewer", "generate", yamlFile)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to generate README: %w", err)
	}

	// Run main steps
	utils.Info("Running main steps...", quiet)
	if err := executor.RunSteps(yamlFile, kubeconfigs, workDir, debug, quiet); err != nil {
		return err
	}

	// Skip extensions if requested
	if noExtensions {
		return nil
	}

	// Find and run extension files
	dir := filepath.Dir(yamlFile)
	pattern := filepath.Join(dir, "skewer-*.yaml")
	extendFiles, err := filepath.Glob(pattern)
	if err != nil {
		return err
	}

	for _, extendFile := range extendFiles {
		if extendFile == yamlFile {
			continue
		}

		utils.Info("\nRunning extension: %s", extendFile, quiet)

		// Create context
		context := &demo.Context{
			WorkDir: workDir,
			Sites:   make(map[string]*demo.SiteContext),
		}

		// Build context from model
		baseModel, err := executor.NewModel(yamlFile, kubeconfigs)
		if err != nil {
			return err
		}

		for _, site := range baseModel.Sites {
			context.Sites[site.Name] = &demo.SiteContext{
				Platform:  site.Platform,
				Env:       site.Env,
				Namespace: site.Namespace,
			}
		}

		// Create and run extended model
		extendedModel, err := demo.CreateExtendedModel(context, extendFile)
		if err != nil {
			return err
		}

		if err := executor.RunSteps(extendedModel.YAMLFile, nil, workDir, debug, quiet); err != nil {
			return err
		}
	}

	return nil
}
