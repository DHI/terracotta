import { createMuiTheme } from '@material-ui/core/styles'

const DHITheme = createMuiTheme({
	palette: {
		primary: {
			main: '#0B4566', // DHI Primary color
		},
		secondary: {
			main: '#00A4EC', // Automatically generated secondary color
			'&:hover': '#0076C8',
		},
		grey: {
			medium: '#DBE4E9',
			light: '#F2F5F7',
			dark: '#86A2B3',
		},
	},
	flexLayout: {
		display: 'flex',
		flexDirection: 'column',
		flex: 1,
	},
	typography: {
		h1: { fontSize: 32, fontWeight: 500 },
		h2: { fontSize: 14, fontWeight: 400 },
		h3: { fontSize: 50, fontWeight: 800 },
		h6: {
			color: '#0B4566',
			fontSize: 14,
			backgroundColor: '#F2F5F7',
			padding: '8px 16px',
		},
		h5: {
			fontSize: 12,
			color: '#0B4566',
		},
		p: {
			fontSize: 12,
		},
		subtitle1: {
			fontSize: 14,
			fontWeight: 600,
			color: '#0B4566',
		},
		body2: {
			fontSize: 12,
		},
	},
	drawerColor: '#ffffff',
	drawerWidth: '50vw',
	overrides: {
		MuiButton: {
			root: {
				color: '#fff',
				fontSize: 12,

				textTransform: 'initial',
				padding: '8px 16px',
			},
			containedSecondary: {
				backgroundColor: '#00A4EC',
				color: '#fff',
				'&:disabled': {
					backgroundColor: 'rgb(242, 245, 247)',
					color: 'rgba(207,219,226)',
				},
				'&:hover': {
					backgroundColor: '#0076C8',
				},
			},
			outlinedPrimary: {
				backgroundColor: ' rgba(0, 164, 236, 0.08)',
				border: '1px solid #00A4EC',
				color: '#0B4566',
			},
			outlinedSecondary: {
				border: '1px solid #DBE4E9',
				color: '#0B4566',
			},
		},
		MuiCardActions: {
			root: {
				padding: 0,
			},
		},
		MuiCardContent: {
			root: {
				padding: 0,
				'&:last-child': {
					paddingBottom: 0,
				},
			},
		},
		MuiCheckbox: {
			root: {
				padding: '0px',
				MuiSvgIcon: {
					root: {
						width: '12px',
					},
				},
			},
		},
		MuiAccordion: {
			root: {
				'&$expanded': {
					margin: 0,
				},
				'&:before': {
					backgroundColor: 'none',
				},
				'&$disabled': {
					backgroundColor: '#f2f5f7',
				},
			},
		},
		MuiAccordionDetails: {
			root: {
				borderBottom: '1px solid #DBE4E9',
			},
		},
		MuiAccordionSummary: {
			content: {
				margin: '8px 0px ',
				'&$expanded': {
					margin: '8px 0px ',
				},
			},
			root: {
				backgroundColor: '#F8F8F8',
				borderBottom: '1px solid #DBE4E9',
				minHeight: 0,
				'&$expanded': {
					minHeight: 0,
					backgroundColor: '#F2F5F7',
				},
				'&:hover': {
					backgroundColor: '#F2F5F7',
				},
			},
		},
		MuiFormControlLabel: {
			root: {
				width: '50%',
				marginLeft: '0px',
				marginRight: '0px',
				'Mui-disabled': {
					'-webkit-text-fill-color': 'rgba(207,219,226)',
					opacity: 1,
				},
			},
			label: {
				fontSize: '12px',
				paddingLeft: '.2rem',
			},
		},
		MuiIconButton: {
			root: {
				padding: 8,
			},
		},
		MuiInputBase: {
			input: {
				fontSize: 12,
				color: '#0B4566',
			},
		},

		MuiPaper: {
			root: {
				color: '#0B4566',
			},
			rounded: {
				borderRadius: 0,
			},
			elevation1: {
				boxShadow: 'none',
			},
			elevation4: {
				boxShadow: 'none',
			},
		},
		MuiSvgIcon: {
			root: {
				width: 16,
				height: 16,
			},
		},
		MuiToolbar: {
			regular: {
				minHeight: 56,
				'@media (min-width: 600px)': {
					minHeight: 56,
				},
			},
		},
		MuiTooltip: {
			tooltip: {
				color: '#fff',
				backgroundColor: '#0B4566',
			},
			arrow: {
				color: '#0B4566',
			},
		},
	},
})

export default DHITheme
