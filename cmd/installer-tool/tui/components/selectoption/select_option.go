package selectoption

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/tui/components"
)

type SelectModel struct {
	choices  map[int]string
    title    string
    footer   []string
    cursor   int
}

func initialModel(choices map[int]string, title string, footer []string) SelectModel {
	return SelectModel{
		choices: choices,
        title: title,
        footer: footer,
		cursor: 0,
	}
}

func (m SelectModel) Init() tea.Cmd {
    // Just return `nil`, which means "no I/O right now, please."
    return nil
}

func (m SelectModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {

    // Is it a key press?
    case tea.KeyMsg:

        // Cool, what was the actual key pressed?
        switch msg.String() {

        // These keys should exit the program.
        case "c":
            return m, tea.Quit

        case "ctrl+c":
            return m, tea.Interrupt

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
        }
    }

    // Return the updated model to the Bubble Tea runtime for processing.
    // Note that we're not returning a command.
    return m, nil
}

func (m SelectModel) View() string {
	var s strings.Builder
    
    components.Title(m.title, &s)

    // Iterate over our choices
    for i := range len(m.choices) {
        // Is the cursor pointing at this choice?
        cursor := " " // no cursor
        if m.cursor == i {
            cursor = ">" // cursor!
        }

        // Is this choice selected?
        checked := false // not selected
        if i == m.cursor {
            checked = true // selected!
        }

		s.WriteString(fmt.Sprintf("%s ", cursor))
        // Render the row
		if checked {
        	s.WriteString(components.CheckedStyle.Render(fmt.Sprintf("%s", m.choices[i])))
		} else {
			s.WriteString(fmt.Sprintf("%s", m.choices[i]))
			
		}
		s.WriteString("\n")
    }

    // Footer
    if len(m.footer) > 0 {
        s.WriteString("\n")
        for i := range m.footer {
            s.WriteString(components.BlurredStyle.Render(m.footer[i]))
            s.WriteString("\n")
        }
    }

	s.WriteString("\n")
    s.WriteString(components.FooterStyle.Render("Press 'c' to continue"))
	s.WriteString("\n")

    // Send the UI for rendering
    return s.String()
}

func SelectList(choices map[int]string, title string, footer []string) (int, error) {
    p := tea.NewProgram(initialModel(choices, title, footer))
	m, err := p.Run(); if err != nil {
        return -1, err
    }
	model := m.(SelectModel)
	return model.cursor, nil
}