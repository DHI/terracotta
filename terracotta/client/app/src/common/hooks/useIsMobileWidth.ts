import useWindowDimensions from './useWindowDimensions'

export default (): boolean => {
	const { width } = useWindowDimensions()

	return width < 600
}
