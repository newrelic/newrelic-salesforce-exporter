package main

import (
	"fmt"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	checkedStyle        = lipgloss.NewStyle().Foreground(lipgloss.Color("#04B575"))
	titleStyle        	= lipgloss.NewStyle().Foreground(lipgloss.Color("#b702a8ff"))
	blurredStyle        = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
)

type model struct {
	choices  []string
    cursor   int
    selected map[int]bool
}

func initialModel() model {
	return model{
		choices:  []string{
			"User Acccess",
			"Apex usage and performance",
			"Lightning usage and performance",
			"API access",
			"Report access",
			"Document, Content and Database access",
			"CRM Analytics (Wave) usage and performance",
			"Errors, Permissions and Violations",
			"Real-time Alerts and Security Warnings (*)",
		},

		selected: make(map[int]bool),

		cursor: 0,
	}
}

func (m model) Init() tea.Cmd {
    // Just return `nil`, which means "no I/O right now, please."
    return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {

    // Is it a key press?
    case tea.KeyMsg:

        // Cool, what was the actual key pressed?
        switch msg.String() {

        // These keys should exit the program.
        case "ctrl+c", "c":
            return m, tea.Quit

        // The "up" and "k" keys move the cursor up
        case "up", "k":
            if m.cursor > 0 {
                m.cursor--
            }

        // The "down" and "j" keys move the cursor down
        case "down", "j":
            if m.cursor < len(m.choices)-1 {
                m.cursor++
            }

        // The "enter" key and the spacebar (a literal space) toggle
        // the selected state for the item that the cursor is pointing at.
        case "enter", " ":
            ok := m.selected[m.cursor]
            if ok {
                delete(m.selected, m.cursor)
            } else {
                m.selected[m.cursor] = true
            }
        }
    }

    // Return the updated model to the Bubble Tea runtime for processing.
    // Note that we're not returning a command.
    return m, nil
}

func (m model) View() string {
	var s strings.Builder
    
    s.WriteString(titleStyle.Render("Select event groups to collect:"))
	s.WriteString("\n\n")

    // Iterate over our choices
    for i, choice := range m.choices {

        // Is the cursor pointing at this choice?
        cursor := " " // no cursor
        if m.cursor == i {
            cursor = ">" // cursor!
        }

        // Is this choice selected?
        checked := " " // not selected
        if _, ok := m.selected[i]; ok {
            checked = "x" // selected!
        }

		s.WriteString(fmt.Sprintf("%s [%s]", cursor, checked))
        // Render the row
		if checked == "x" {
        	s.WriteString(checkedStyle.Render(fmt.Sprintf(" %s", choice)))
		} else {
			s.WriteString(fmt.Sprintf(" %s", choice))
			
		}
		s.WriteString("\n")
    }

    // The footer
	s.WriteString("\n")
    s.WriteString(blurredStyle.Render("(*) This group requires rolling out a separate data collector and access to the Salesforce Event Stream."))
	s.WriteString("\n")
	s.WriteString("\n")
    s.WriteString("Press 'c' to continue.")
	s.WriteString("\n")

    // Send the UI for rendering
    return s.String()
}

func main() {
    p := tea.NewProgram(initialModel())
	_, err := p.Run(); if err != nil {
        fmt.Printf("Alas, there's been an error: %v", err)
        os.Exit(1)
    }
}