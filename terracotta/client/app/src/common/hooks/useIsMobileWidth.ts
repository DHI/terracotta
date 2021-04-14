import useWindowDimensions from './useWindowDimensions'
/* eslint-disable */
export default (): boolean => {

	const { width } = useWindowDimensions()

	return width < 600

}
