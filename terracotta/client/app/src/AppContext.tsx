import { createContext } from 'react'
import { Viewport } from "./map/types"
interface AppContextValues {
	state: {
        viewport: Viewport,
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
