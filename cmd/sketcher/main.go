package main

import (
	"fmt"
	"os"

	"github.com/skupperproject/sketcher/internal/cli"
)

const version = "0.2.0"

func main() {
	if err := cli.Execute(version); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
