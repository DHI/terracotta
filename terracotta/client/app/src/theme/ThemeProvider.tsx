import React, { useMemo, FC, ReactNode } from 'react'
import { ComponentsOverrides, ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { PaletteMode } from '@mui/material'
import getDhiSharedTheme from './getDhiSharedTheme'

export interface ThemeProviderProps {
	overrides?: ComponentsOverrides
	children?: ReactNode
	mode?: PaletteMode
}

const DHIThemeProvider: FC<ThemeProviderProps> = ({
	overrides = {},
	children,
	mode = 'light',
}) => {
	const theme = useMemo(
		() =>
			getDhiSharedTheme(mode, {
				...overrides,
			}),
		[overrides],
	)
	return (
		<>
			<ThemeProvider theme={theme}>
				<CssBaseline />
				{children}
			</ThemeProvider>
		</>
	)
}

export default DHIThemeProvider
