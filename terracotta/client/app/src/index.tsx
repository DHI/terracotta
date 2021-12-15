import React from 'react'
import ReactDOM from 'react-dom'
import App from './App'
import { ThemeProvider } from "@material-ui/core"
import DhiTheme from "./theme/theme"

require('dotenv').config()

ReactDOM.render(
	<React.StrictMode>
		<ThemeProvider theme={DhiTheme}>
			<App hostnameProp={document.getElementById('hostname-id')?.innerText}/>
		</ThemeProvider>
	</React.StrictMode>,
	document.getElementById('root')
)
