package components

import (
	"strings"

	"github.com/charmbracelet/lipgloss"
)

var (
	CheckedStyle	= lipgloss.NewStyle().Foreground(lipgloss.Color("#04B575"))
	TitleStyle		= lipgloss.NewStyle().Foreground(lipgloss.Color("#b904aaff")).MarginLeft(2)
	BlurredStyle	= lipgloss.NewStyle().Foreground(lipgloss.Color("240")).MarginLeft(2)
	FooterStyle		= lipgloss.NewStyle().MarginLeft(2)
	NoStyle			= lipgloss.NewStyle()
)

func Title(title string, s *strings.Builder) *strings.Builder {
	if s == nil {
		s = &strings.Builder{}
	}
    s.WriteString(TitleStyle.Render(title))
    s.WriteString("\n")
    s.WriteString(TitleStyle.Render(strings.Repeat("-", len(title))))
    
	s.WriteString("\n\n")

	return s
}