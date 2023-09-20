import { PaletteMode } from '@mui/material'
import { Components, createTheme } from '@mui/material/styles'
import getDhiPallete from './getDhiPalette'

const FONT_FAMILY = [
	'Roboto',
	'-apple-system',
	'BlinkMacSystemFont',
	'Arial',
	'sans-serif',
].join(',')

const defaultTheme = createTheme()

const getDhiOverrides = (mode: PaletteMode): Components => {
	const dhiPalette = getDhiPallete(mode)
	return {
		MuiCssBaseline: {
			styleOverrides: {
				'*::-webkit-scrollbar': {
					width: '8px',
					height: '8px',
					backgroundColor: dhiPalette.grey[100],
					borderRadius: '100px',
				},
				'*::-webkit-scrollbar:hover': {
					backgroundColor: 'rgba(0, 0, 0, 0.2)',
				},
				'*::-webkit-scrollbar-thumb': {
					backgroundColor: dhiPalette.grey[500],
					WebkitBorderRadius: '100px',
				},
				'*::-webkit-scrollbar-thumb:active': {
					backgroundColor: dhiPalette.grey[500],
					WebkitBorderRadius: '100px',
				},
			},
		},
		MuiTypography: {
			styleOverrides: {
				root: {
					fontFamily: FONT_FAMILY,
				},
			},
		},
		MuiAppBar: {
			styleOverrides: {
				colorPrimary: {
					backgroundColor: dhiPalette.grey[50],
					height: '60px',
					borderBottom: `4px solid ${dhiPalette.grey[100]}`,
				},
			},
		},
		MuiToolbar: {
			styleOverrides: {
				// not sure if this is really desireable
				root: {
					height: '60px',
					minHeight: '0 !important',
				},
			},
		},
		MuiDialog: {
			styleOverrides: {
				container: {
					'& .MuiPickersModal-dialogRoot': {
						border: `1px solid ${dhiPalette.divider}`,
					},
				},
			},
		},
		MuiDialogContent: {
			styleOverrides: {
				root: {},
			},
		},
		MuiDialogTitle: {
			styleOverrides: {
				root: {
					paddingTop: 24,
				},
			},
		},
		MuiDialogContentText: {
			styleOverrides: {
				root: {
					color: dhiPalette.text.primary,
				},
			},
		},
		MuiDialogActions: {
			styleOverrides: {
				root: {},
			},
		},
		MuiButton: {
			styleOverrides: {
				root: {
					fontWeight: 700,
					letterSpacing: 0.1,
					textTransform: 'none',
					borderRadius: '4px',
					height: '2.5rem', // 40px
				},
				sizeLarge: {
					minHeight: '3rem', // 48px
				},
				sizeSmall: {
					height: '2rem', // 40px
					minWidth: 0,
					padding: '0 1rem', // 16px
				},
				outlined: {
					border: '2px solid !important',
				},
				outlinedPrimary: {
					'&:hover': {
						borderColor: `${dhiPalette.primary.dark}`,
					},
				},
				outlinedSecondary: {
					'&:hover': {
						borderColor: `${dhiPalette.secondary.dark}`,
					},
				},
			},
		},
		MuiBadge: {
			styleOverrides: {
				colorPrimary: {
					backgroundColor: dhiPalette.error.main,
				},
			},
		},
		MuiFab: {
			styleOverrides: {
				primary: {
					backgroundColor: dhiPalette.primary.main,
					color: dhiPalette.background.paper,
					'&:hover': {
						backgroundColor: dhiPalette.primary.dark,
					},
				},
				secondary: {
					backgroundColor: dhiPalette.secondary.main,
					color: dhiPalette.background.paper,
					'&:hover': {
						backgroundColor: dhiPalette.secondary.dark,
					},
				},
			},
		},
		MuiSvgIcon: {
			styleOverrides: {
				colorPrimary: {
					color: dhiPalette.text.primary,
				},
			},
		},
		MuiInputBase: {
			styleOverrides: {
				input: {
					'&.Mui-disabled': {
						color: dhiPalette.grey[200],
					},
				},
			},
		},
		MuiFilledInput: {
			styleOverrides: {
				input: {
					'&.Mui-disabled': {
						backgroundColor: dhiPalette.grey[50],
					},
				},
			},
		},
		MuiOutlinedInput: {
			styleOverrides: {
				input: {
					'&.Mui-disabled': {
						backgroundColor: dhiPalette.grey[50],
					},
				},
			},
		},
		MuiTable: {
			styleOverrides: {
				root: { overflowX: 'auto' },
			},
		},
		MuiTableCell: {
			styleOverrides: {
				body: {
					height: '44px',
					color: dhiPalette.text.primary,
					padding: '0',
					width: '300px',
				},
				head: {
					padding: '0',
					height: '44px',
					backgroundColor: dhiPalette.background.paper,
					borderBottom: `2px solid ${dhiPalette.divider}`,
					cursor: 'pointer ',
				},
			},
		},
		MuiTableRow: {
			styleOverrides: {
				root: {
					'&:hover, &:focus': {
						backgroundColor: dhiPalette.grey[50],
					},
				},
			},
		},
		MuiStepper: {
			styleOverrides: {
				root: {
					padding: '0.5rem', // 8px
				},
			},
		},
		MuiStepConnector: {
			styleOverrides: {
				line: {
					borderColor: dhiPalette.text.secondary,
				},
			},
		},
		MuiStepIcon: {
			styleOverrides: {
				root: {
					fill: dhiPalette.background.paper,
					color: dhiPalette.text.secondary,
					border: 'solid',
					borderColor: dhiPalette.text.secondary,
					borderRadius: 25,
					borderWidth: 1,
					'&.Mui-active': {
						border: 'none',
						fill: dhiPalette.secondary.main,
						'& .MuiStepIcon-text': {
							fill: `${dhiPalette.background.paper}`,
						},
					},
					'&.Mui-completed': {
						border: 'none',
						fill: dhiPalette.secondary.main,
					},
				},
				text: {
					fill: dhiPalette.text.secondary,
					fontSize: 15, // for vertical alignment
				},
			},
		},
		MuiTooltip: {
			styleOverrides: {
				arrow: {
					color: dhiPalette.primary.main,
				},
				tooltip: {
					backgroundColor: dhiPalette.grey[200],
					color: dhiPalette.text.primary,
				},
			},
		},
		MuiSwitch: {
			styleOverrides: {
				// colorPrimary: {
				//   '&.Mui-disabled': {
				//     '&.Mui-checked': {
				//       color: dhiPalette.primary.light,
				//       '& .Mui-track': {
				//         backgroundColor: dhiPalette.primary.light,
				//         opacity: 0.5,
				//       },
				//     },
				//   },
				// },
				// colorSecondary: {
				//   '&.Mui-disabled': {
				//     '&.Mui-checked': {
				//       color: dhiPalette.secondary.light,
				//       '& .Mui-track': {
				//         backgroundColor: dhiPalette.secondary.light,
				//         opacity: 0.5,
				//       },
				//     },
				//   },
				// },
			},
		},
		MuiTab: {
			styleOverrides: {
				root: {
					[defaultTheme.breakpoints.up('xs')]: {
						fontSize: '0.75rem', // 12px
						fontWeight: 'normal',
						paddingLeft: '0.75rem', // 12px
						paddingRight: '0.75rem',
						minWidth: '0',
					},
					'&:hover, &:focus': {
						color: dhiPalette.primary.main,
					},
					'&.Mui-selected': {
						fontWeight: 'bold', // todo hevo: should we use theme.typography.fontWeight instead?
					},
				},
			},
		},
		MuiTabs: {
			styleOverrides: {
				scrollButtons: {
					[defaultTheme.breakpoints.up('xs')]: {
						minWidth: 0,
						width: 'auto',
						'& svg': {
							width: 40,
						},
					},
				},
			},
		},
		MuiAccordion: {
			styleOverrides: {
				root: {
					'& .MuiAccordionSummary-root.Mui-expanded': {
						backgroundColor: dhiPalette.grey[50],
						minHeight: '50px',
					},
					'& .MuiAccordionSummary-content.Mui-expanded': {
						margin: 0,
					},
					'& .MuiAccordionSummary-root.Mui-disabled': {
						opacity: 0.4,
					},
					'& .MuiAccordionSummary-root': {
						'& .MuiTypography-root': {
							fontWeight: 700,
						},
						'&:not(.Mui-expanded):hover': {
							backgroundColor: `${dhiPalette.primary.main}10`,
						},
						'&.Mui-expanded:hover': {
							backgroundColor: `${dhiPalette.secondary.light}80`,
						},
					},
					'& .MuiAccordionSummary-expandIconWrapper .MuiSvgIcon-root': {
						fill: dhiPalette.secondary.dark,
					},
					'& .MuiAccordionDetails-root': {
						backgroundColor: dhiPalette.grey[50],
					},
				},
			},
		},
		MuiSlider: {
			styleOverrides: {
				valueLabel: {
					backgroundColor: dhiPalette.grey[200],
					color: dhiPalette.text.primary,
				},
			},
		},
	}
}

export default getDhiOverrides
