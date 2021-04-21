// eslint-disable-next-line @typescript-eslint/no-unused-vars
import React from 'react'
import { Switch as MuiSwitch } from '@material-ui/core'
import { withStyles } from '@material-ui/core/styles'

const Switch = withStyles(() => ({
	root: {
		width: 36,
		height: 12,
		padding: 0,
		display: 'flex',
		flexDirection: 'row',
		alignItems: 'center',
		overflow: 'inherit',
		float: 'right',
	},
	switchBase: {
		padding: 0,
		height: '100%',
		color: '#86A2B3 !important',
		transform: 'translateX(4px)',
		'&:hover': {
			backgroundColor: 'transparent',
		},
		'&$checked': {
			transform: 'translateX(22px)',
			color: '#61C051 !important',
			height: '100%',
			'& + $track': {
				opacity: 1,
				backgroundColor: '#BFE787 !important',
				borderColor: '#BFE787 !important',
			},
			'&:hover': {
				backgroundColor: 'transparent',
			},
		},
	},
	input: {
		left: '-50%',
		'&:checked': {
			left: '-150%',
		},
	},
	thumb: {
		width: 10,
		height: 10,
		boxShadow: 'none',
	},
	track: {
		border: '2px solid #86A2B3 !important',
		borderRadius: 20 / 2,
		opacity: 1,
		backgroundColor: '#FFF',
	},
	checked: {},
}))(MuiSwitch)

export default Switch
