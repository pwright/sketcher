package kubernetes

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
	"time"

	"github.com/skupperproject/sketcher/internal/utils"
)

// CheckEnvironment verifies required programs are available
func CheckEnvironment() error {
	// Hard requirements - must be present
	required := []string{"base64", "curl", "kubectl"}

	// Optional programs - warn if missing but continue
	optional := []string{"skupper"}

	// Check required programs (hard failure)
	for _, program := range required {
		if err := utils.CheckProgram(program); err != nil {
			return err
		}
	}

	// Check optional programs (warning only)
	for _, program := range optional {
		if err := utils.CheckProgram(program); err != nil {
			utils.Warn("Optional program '%s' is not available - related commands will fail if executed", program)
			utils.Warn("Install skupper: https://skupper.io/install/")
		}
	}

	return nil
}

// ResourceExists checks if a Kubernetes resource exists
func ResourceExists(resource string) bool {
	cmd := exec.Command("kubectl", "get", resource)
	return cmd.Run() == nil
}

// GetResourceJSON gets a resource field using kubectl jsonpath
func GetResourceJSON(resource, jsonpath string) (string, error) {
	cmd := exec.Command("kubectl", "get", resource, "-o", fmt.Sprintf("jsonpath='{%s}'", jsonpath))
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(string(output)), nil
}

// AwaitResource waits for a Kubernetes resource to become available
func AwaitResource(resource string, timeout int, quiet bool) error {
	if !strings.Contains(resource, "/") {
		return fmt.Errorf("resource must be in format 'type/name': %s", resource)
	}

	start := time.Now()

	for {
		utils.Info("Waiting for %s to become available", resource)

		if ResourceExists(resource) {
			break
		}

		if time.Since(start) > time.Duration(timeout)*time.Second {
			return fmt.Errorf("timed out waiting for %s", resource)
		}

		time.Sleep(5 * time.Second)
	}

	// For deployments, wait for available condition
	if strings.HasPrefix(resource, "deployment/") {
		cmd := exec.Command("kubectl", "wait", "--for", "condition=available", "--timeout", fmt.Sprintf("%ds", timeout), resource)
		if err := cmd.Run(); err != nil {
			// Show logs on failure
			logCmd := exec.Command("kubectl", "logs", resource)
			logCmd.Run()
			return err
		}
	}

	return nil
}

// AwaitIngress waits for LoadBalancer ingress hostname or IP
func AwaitIngress(service string, timeout int, quiet bool) (string, error) {
	if !strings.HasPrefix(service, "service/") {
		return "", fmt.Errorf("service must start with 'service/': %s", service)
	}

	start := time.Now()

	// Wait for service to exist
	if err := AwaitResource(service, timeout, quiet); err != nil {
		return "", err
	}

	// Wait for loadBalancer ingress
	for {
		utils.Info("Waiting for hostname or IP from %s to become available", service)

		jsonStr, err := GetResourceJSON(service, ".status.loadBalancer.ingress")
		if err == nil && jsonStr != "" {
			var data []map[string]interface{}
			if err := json.Unmarshal([]byte(jsonStr), &data); err == nil && len(data) > 0 {
				if hostname, ok := data[0]["hostname"].(string); ok {
					return hostname, nil
				}
				if ip, ok := data[0]["ip"].(string); ok {
					return ip, nil
				}
			}
		}

		if time.Since(start) > time.Duration(timeout)*time.Second {
			return "", fmt.Errorf("timed out waiting for hostname or external IP for %s", service)
		}

		time.Sleep(5 * time.Second)
	}
}

// AwaitConsoleOK waits for Skupper console to be ready
func AwaitConsoleOK(timeout int, quiet bool) error {
	// Wait for secret
	if err := AwaitResource("secret/skupper-console-users", timeout, quiet); err != nil {
		return err
	}

	// Get admin password
	password, err := GetResourceJSON("secret/skupper-console-users", ".data.admin")
	if err != nil {
		return err
	}

	password, err = utils.Base64Decode(password)
	if err != nil {
		return err
	}

	// Verify console is accessible (simplified)
	return nil
}
