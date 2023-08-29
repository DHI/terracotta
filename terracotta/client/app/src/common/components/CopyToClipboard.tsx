import React, { CSSProperties, useState, FC } from 'react'
import { Grid, SxProps, Tooltip } from '@mui/material'
import FileCopyOutlinedIcon from '@mui/icons-material/FileCopyOutlined'
import Clipboard from 'react-clipboard.js'

const disabledStyle = {
	// borderBottom: '1px solid #cfdbe2',
	color: '#cfdbe2',
	cursor: 'no-drop',
}

const enabledStyle = {
	// borderBottom: '1px solid #0b4566',
	color: '#0b4566',
	cursor: 'pointer',
}

export type CopyToClipboardProps = {
	disabled?: boolean
	helperText?: string
	url?: boolean
	message?: string
	sx?: SxProps
	className?: string | undefined
}

export const mockCopy: VoidFunction = () => {
	// call this function
}

const CopyToClipboard: FC<CopyToClipboardProps> = ({
	disabled = false,
	helperText = '',
	message = '',
	sx = {},
	className,
}) => {
	const [copyUrl] = useState(window.location.href)
	const [tooltip, setTooltip] = useState(
		helperText || (message ? 'Copy text' : 'Copy URL'),
	)

	const copyAction = () => {
		// mockCopy();
		if (message) {
			setTooltip('Text copied to Clipboard.')
			setTimeout(() => {
				setTooltip(helperText || 'Copy text')
			}, 5000)
		} else {
			setTooltip('URL copied to Clipboard.')
			setTimeout(() => {
				setTooltip(helperText || 'Copy URL')
			}, 5000)
		}
	}

	const copy = () => {
		if (disabled !== true) {
			copyAction()
		}
	}

	return (
		<Grid
			alignItems="flex-end"
			justifyContent="space-between"
			spacing={0}
			sx={
				disabled === true
					? { ...sx, ...disabledStyle }
					: { ...sx, ...enabledStyle }
			}
			container
			onClick={() => copy()}
		>
			<Grid item>
				<Grid alignItems="center" justifyContent="center" container>
					<Tooltip title={tooltip}>
						<FileCopyOutlinedIcon color="primary" sx={{ cursor: 'pointer' }} />
					</Tooltip>
				</Grid>
			</Grid>
		</Grid>
	)
}

export default CopyToClipboard
