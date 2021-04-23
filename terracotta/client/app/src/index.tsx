import React from 'react'
import ReactDOM from 'react-dom'
import App from './App'
import { ThemeProvider } from "@material-ui/core"
import GRASTheme from "./theme/theme"

ReactDOM.render(
	<React.StrictMode>
		<ThemeProvider theme={GRASTheme}>
			<App hostnameProp={document.getElementById('hostname-id')?.innerText}/>
		</ThemeProvider>
	</React.StrictMode>,
	document.getElementById('root')
)
