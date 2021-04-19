import { createContext } from 'react'
import { Viewport } from "./map/types"
interface AppContextValues {
	state: {
        viewport: Viewport,
        isOpticalBasemap: boolean,
		hostname: string | undefined,
		keys: string[] | undefined
	},
	actions: {
		setIsOpticalBasemap: Function,
        setViewport: Function,
		setKeys: Function
	},
}

type Context = AppContextValues

const AppContext = createContext<Context>(null as any)

export default AppContext
