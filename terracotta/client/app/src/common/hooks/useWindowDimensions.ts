import { useState, useEffect } from 'react'
/* eslint-disable */
const getWindowDimensions = () => {

	const { clientWidth: width, clientHeight: height } = document.body

	return {
		width,
		height,
	}

}

interface ReturnType {
	width: number,
	height: number,
}
export default (): ReturnType => {

	const [ windowDimensions, setWindowDimensions ] = useState(
		getWindowDimensions(),
	)

	useEffect(() => {

		const handleResize = () => {

			setWindowDimensions(getWindowDimensions())

		}

		window.addEventListener('resize', handleResize)

		return () => window.removeEventListener('resize', handleResize)

	}, [])

	return windowDimensions

}
