package components

import "github.com/charmbracelet/lipgloss"

var (
	CheckedStyle	= lipgloss.NewStyle().Foreground(lipgloss.Color("#04B575"))
	TitleStyle		= lipgloss.NewStyle().Foreground(lipgloss.Color("#b904aaff")).MarginLeft(2)
	BlurredStyle	= lipgloss.NewStyle().Foreground(lipgloss.Color("240")).MarginLeft(2)
	FooterStyle		= lipgloss.NewStyle().MarginLeft(2)
)