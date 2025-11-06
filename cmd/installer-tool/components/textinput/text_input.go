package textinput

import (
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	focusedStyle        = lipgloss.NewStyle().Foreground(lipgloss.Color("205"))
	cursorStyle         = focusedStyle
)

type InputModel struct {
	input      textinput.Model
}

func initialModel() InputModel {
	m := InputModel{
		input: textinput.Model{},
	}

	var t textinput.Model
	t = textinput.New()
	t.Cursor.Style = cursorStyle
	t.CharLimit = 32
	t.Placeholder = "Nickname"
	t.Focus()
	t.PromptStyle = focusedStyle
	t.TextStyle = focusedStyle

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
	var b strings.Builder

	b.WriteString(m.input.View())
	b.WriteRune('\n')

	return b.String()
}

func TextInput() (string, error) {
	m, err := tea.NewProgram(initialModel()).Run(); if err != nil {
		return "", err
	}
	model := m.(InputModel)
	return model.input.Value(), nil
}