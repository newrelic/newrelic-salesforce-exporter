package checkerlist

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components"
)

type CheckerModel struct {
	choices  map[int]string
    title    string
    footer   []string
    cursor   int
    selected map[int]bool
}

func initialModel(choices map[int]string, title string, footer []string) CheckerModel {
	return CheckerModel{
		choices: choices,
        title: title,
        footer: footer,
		selected: make(map[int]bool),
		cursor: 0,
	}
}

func (m CheckerModel) Init() tea.Cmd {
    // Just return `nil`, which means "no I/O right now, please."
    return nil
}

func (m CheckerModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
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

func (m CheckerModel) View() string {
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
        checked := " " // not selected
        if _, ok := m.selected[i]; ok {
            checked = "x" // selected!
        }

		s.WriteString(fmt.Sprintf("%s [%s]", cursor, checked))
        // Render the row
		if checked == "x" {
        	s.WriteString(components.CheckedStyle.Render(fmt.Sprintf(" %s", m.choices[i])))
		} else {
			s.WriteString(fmt.Sprintf(" %s", m.choices[i]))
			
		}
		s.WriteString("\n")
    }

    // Footer
	s.WriteString("\n")
    for i := range m.footer {
        s.WriteString(components.BlurredStyle.Render(m.footer[i]))
        s.WriteString("\n")
    }

	s.WriteString("\n")
    s.WriteString(components.FooterStyle.Render("Press 'c' to continue"))
	s.WriteString("\n")

    // Send the UI for rendering
    return s.String()
}

func CheckerList(choices map[int]string, title string, footer []string) ([]int, error) {
    p := tea.NewProgram(initialModel(choices, title, footer))
	m, err := p.Run(); if err != nil {
        return nil, err
    }
	model := m.(CheckerModel)
	checked := []int{}
	for pos := range model.selected {
		if model.selected[pos] {
			checked = append(checked, pos)
		}
	}
	return checked, nil
}