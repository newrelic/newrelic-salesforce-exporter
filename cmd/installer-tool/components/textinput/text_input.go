package textinput

import (
	"strings"

	"github.com/charmbracelet/bubbles/cursor"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/newrelic/newrelic-salesforce-exporter/cmd/installer-tool/components"
)

type InputModel struct {
	label       string
	input       textinput.Model
}

func initialModel(label string, initial string) InputModel {
	m := InputModel{
		label: label,
		input: textinput.Model{},
	}

	var t textinput.Model
	t = textinput.New()
	t.Cursor.Style = components.BlurredStyle
	t.Cursor.SetMode(cursor.CursorStatic)
	t.CharLimit = 256
	t.Placeholder = ""
	t.Focus()
	t.PromptStyle = components.CheckedStyle.MarginLeft(2)
	t.Prompt = label + ": "
	t.TextStyle = components.NoStyle
	t.SetValue(initial)

	m.input = t

	return m
}

func (m InputModel) Init() tea.Cmd {
	return textinput.Blink
}

func (m InputModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
        case "ctrl+c":
            return m, tea.Interrupt
			
		case "enter", "esc":
			return m, tea.Quit
		}
	}

	// Handle character input and blinking
	cmd := m.updateInputs(msg)

	return m, cmd
}

func (m *InputModel) updateInputs(msg tea.Msg) tea.Cmd {
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)

	return tea.Batch(cmd)
}

func (m InputModel) View() string {
	var s strings.Builder

	s.WriteString(m.input.View())
	s.WriteRune('\n')

	return s.String()
}

func TextInput(label string, initial string) (string, error) {
	m, err := tea.NewProgram(initialModel(label, initial)).Run(); if err != nil {
		return "", err
	}
	model := m.(InputModel)
	return model.input.Value(), nil
}