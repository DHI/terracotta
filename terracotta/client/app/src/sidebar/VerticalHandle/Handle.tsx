import React, { MouseEventHandler, FC } from 'react'
import clsx from 'clsx'
import { Box } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { DragHandle as DragHandleIcon, ExpandLess as ExpandLessIcon } from '@material-ui/icons'

const useStyles = makeStyles(theme => ({
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
		color: theme.palette.primary.main,
		transform: 'translate(0, -2px)',
	},
	iconBox: {
		zIndex: 10,
		padding: theme.spacing(1, 1, 0.1, 1),
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
}))

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

	const classes = useStyles()

	return (
		<Box
			draggable={false}
			onMouseDown={onMouseDown}
			onMouseUp={onMouseUp}
			className={clsx(classes.root, isCollapsed && classes.collapsedRoot)}
			onClick={() => isCollapsed && onClickExpand()}
		>
			<Box draggable={false} className={classes.iconBox}>
				{!isCollapsed ?
					<DragHandleIcon className={classes.icon}/> :
					<ExpandLessIcon className={classes.icon} />
			}
			</Box>
		</Box>
	)

}

export default Handle
