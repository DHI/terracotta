import React, {
	useEffect, useState, FC, ReactNode, useContext,
} from 'react'
import ReactMapGL, { FlyToInterpolator } from 'react-map-gl'
import ZoomControl from './MapZoomControl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { easeCubicInOut } from 'd3-ease'
import useIsMobileWidth from '../common/hooks/useIsMobileWidth'
import AppContext from "../AppContext"

const accessToken = 'pk.eyJ1Ijoiam9zbGRoaSIsImEiOiJja2d0ZjdzbXAwMXdxMnNwN2Jkb2NvbXJ3In0.SayFfMYF2huWsZckbqNqEw'

const Map: FC = () => {

	const isMobile = useIsMobileWidth()
	const {
		state: { isOpticalBasemap, viewport },
		actions: { setViewport }
	} = useContext(AppContext)

	const [ localViewport, setLocalViewport ] = useState<any | undefined>(
		undefined,
	)
	const basemap = isOpticalBasemap ? 'mapbox://styles/mapbox/satellite-v9' : 'mapbox://styles/mapbox/light-v10'
	
	useEffect(() => {

		const { latitude, longitude, zoom } = viewport
		setLocalViewport({
			...{
				longitude,
				latitude,
				zoom,
				transitionDuration: 2000,
				transitionInterpolator: new FlyToInterpolator(),
				transitionEasing: easeCubicInOut,
			},
		})


	}, [ viewport ])

	return (
		<ReactMapGL
			{...localViewport}
			width={'100%'}
			height={'100%'}
			mapboxApiAccessToken={accessToken}
			mapStyle={basemap}
			onViewportChange={setLocalViewport}
		>
			{!isMobile && (
				<ZoomControl />
			)}
			
		</ReactMapGL>
	)

}

export default Map
