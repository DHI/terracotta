import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import DHIThemeProvider from './theme/ThemeProvider'

const container = document.getElementById('root')
const root = container && createRoot(container)

const hostname = document.getElementById('hostname-id')?.innerText

root?.render(
	<React.StrictMode>
		<DHIThemeProvider>
			<App hostnameProp={hostname} />
		</DHIThemeProvider>
	</React.StrictMode>,
)
