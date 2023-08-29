import { PaletteOptions, createTheme } from '@mui/material/styles'
import { PaletteMode } from '@mui/material'
import dhiTypography from './dhiTypography'
import getDhiPalette from './getDhiPalette'
import getDhiOverrides from './getDhiOverrides'

const getDhiTheme = (
	mode: PaletteMode,
	overrides?: Record<string, unknown> | undefined,
) =>
	createTheme(
		{
			typography: dhiTypography,
			palette: getDhiPalette(mode) as any as PaletteOptions,
			components: getDhiOverrides(mode),
		},
		overrides as any,
	)

export default getDhiTheme
