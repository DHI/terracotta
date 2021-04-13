import { createContext } from 'react'

interface AppContextValues {
	state: {
        viewport: any,
        isOpticalBasemap: boolean
	},
	actions: {
		setIsOpticalBasemap: Function,
        setViewport: Function
	},
}

type Context = AppContextValues

const AppContext = createContext<Context>(null as any)

export default AppContext
