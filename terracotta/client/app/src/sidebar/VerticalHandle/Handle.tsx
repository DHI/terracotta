import React, { MouseEventHandler, FC } from 'react'
import { Box } from '@mui/material'
import {
	DragHandle as DragHandleIcon,
	ExpandLess as ExpandLessIcon,
} from '@mui/icons-material'

const styles = {
	root: {
		height: '100%',
		width: 2,
		background: '#557A8F',
		cursor: 'e-resize',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-around',
	},
	collapsedRoot: {
		cursor: 'pointer',
	},
	icon: {
		color: 'secondary.main',
		transform: 'translate(0, -2px)',
	},
	iconBox: {
		zIndex: 10,
		p: 2,
		pb: 1,
		transform: 'translate(-40%, 0) rotate(-90deg)',
		width: 20,
		height: 20,
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-around',
		background: '#85A2B3',
		position: 'relative',
		borderRadius: '20px 20px 0 0',
	},
}

interface Props {
	onMouseUp: MouseEventHandler<HTMLDivElement> | undefined
	onMouseDown: MouseEventHandler<HTMLDivElement> | undefined
	isCollapsed: boolean
	onClickExpand: () => void
}

const Handle: FC<Props> = ({
	onMouseDown,
	onMouseUp,
	isCollapsed,
	onClickExpand,
}) => (
	<Box
		component="div"
		sx={{
			...styles.root,
			...(isCollapsed ? { cursor: styles.collapsedRoot } : {}),
		}}
		onClick={() => isCollapsed && onClickExpand()}
		onMouseDown={onMouseDown}
		onMouseUp={onMouseUp}
	>
		<Box draggable={false} sx={styles.iconBox}>
			{!isCollapsed ? (
				<DragHandleIcon sx={styles.icon} />
			) : (
				<ExpandLessIcon sx={styles.icon} />
			)}
		</Box>
	</Box>
)

export default Handle
