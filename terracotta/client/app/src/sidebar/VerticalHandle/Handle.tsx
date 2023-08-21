import React, { MouseEventHandler, FC } from 'react'
import { Box, Theme } from '@mui/material'
import { DragHandle as DragHandleIcon, ExpandLess as ExpandLessIcon } from '@mui/icons-material'

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
		color: "primary.main",
		transform: 'translate(0, -2px)',
	},
	iconBox: {
		zIndex: 10,
		padding: (theme: Theme) => theme.spacing(1, 1, 0.1, 1),
		transform: 'translate(-40%, 0) rotate(-90deg)',
		width: 20,
		height: 15,
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-around',
		background: '#85A2B3',
		position: 'relative',
		borderRadius: '20px 20px 0 0',
	},
}

interface Props {
	onMouseUp: MouseEventHandler<HTMLElement> | undefined,
	onMouseDown: MouseEventHandler<HTMLElement> | undefined,
	isCollapsed: boolean,
	onClickExpand: () => void
}

const Handle: FC<Props> = ({
	onMouseDown,
	onMouseUp,
	isCollapsed,
	onClickExpand
}) => {

	return (
		<Box
			draggable={false}
			onMouseDown={onMouseDown}
			onMouseUp={onMouseUp}
			sx={{
				...styles.root,
				...(!isCollapsed && { cursor: styles.collapsedRoot }),
			}}
			onClick={() => isCollapsed && onClickExpand()}
		>
			<Box draggable={false} sx={styles.iconBox}>
				{!isCollapsed ?
					<DragHandleIcon sx={styles.icon}/> :
					<ExpandLessIcon sx={styles.icon} />
			}
			</Box>
		</Box>
	)

}

export default Handle
