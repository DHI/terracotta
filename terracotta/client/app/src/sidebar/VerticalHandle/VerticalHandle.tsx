import React, { useState, useEffect, useCallback, FC } from 'react'
import Handle from './Handle'

const minWidth = 0
const minMapWidth = 50

interface Props{
	boxWidth: number,
	onDrag: (w: number) => void,
}

const VerticalHandle: FC<Props> = ({
	boxWidth,
	onDrag,
}) => {
	console.log(boxWidth)
	const [ isDragging, setIsDragging ] = useState(false)
	const [ initialWidth, setInitialWidth ] = useState(minWidth * 2)

	const handleMouseMove = useCallback(e => {

		const windowWidth = window.innerWidth
		const w = e.clientX < minMapWidth ?
			windowWidth - minMapWidth :
			windowWidth - e.clientX

		onDrag(w)

	}, [ onDrag ])

	const handleMouseDown = useCallback(e => {

		setIsDragging(true)
		const w = window.innerWidth - e.clientX
		setInitialWidth(initialWidth < minWidth ? minWidth : w)

	}, [  initialWidth ])

	const handleMouseUp = useCallback(() => {

		if (boxWidth < minWidth) {

			onDrag(initialWidth)

		}

		if(boxWidth < 300){
			onDrag(0)
		}

		setIsDragging(false)

	}, [ boxWidth, initialWidth, onDrag ])

	useEffect(() => {

		const remove = () => {

			window.removeEventListener('mousemove', handleMouseMove)
			window.removeEventListener('mouseup', handleMouseUp)
			window.removeEventListener('mousedown', handleMouseDown)

		}

		const add = () => {

			window.addEventListener('mousedown', handleMouseDown)
			window.addEventListener('mousemove', handleMouseMove)
			window.addEventListener('mouseup', handleMouseUp)

		}

		if (isDragging) add()
		else remove()

		return remove

	}, [ isDragging, handleMouseMove, handleMouseDown, handleMouseUp ])

	return (
		<Handle
			onMouseDown={handleMouseDown}
			onMouseUp={() => setIsDragging(false)}
			isCollapsed={boxWidth < 10}
			onClickExpand={() => onDrag(30/100 * window.innerWidth)}
		/>
	)

}

export default VerticalHandle
