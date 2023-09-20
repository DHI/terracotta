import React, { useState, FC } from 'react'
import { IconButton, Tooltip } from '@mui/material'
import FileCopyOutlinedIcon from '@mui/icons-material/FileCopyOutlined'

export type CopyToClipboardProps = {
	disabled?: boolean
	helperText?: string
	url?: boolean
	message: string
}

const CopyToClipboard: FC<CopyToClipboardProps> = ({
	disabled = false,
	helperText,
	message,
	url,
}) => {
	const [tooltip, setTooltip] = useState(
		helperText || (message ? 'Copy text' : 'Copy URL'),
	)

	const copyAction = async () => {
		await navigator.clipboard.writeText(message)

		setTooltip(`${url ? 'URL' : 'Text'} copied to Clipboard.`)
		setTimeout(() => {
			setTooltip(helperText || `Copy ${url ? 'URL' : 'Text'}`)
		}, 3000)
	}

	const copy = () => {
		if (!disabled) {
			void copyAction()
		}
	}

	return (
		<Tooltip title={tooltip}>
			<IconButton disabled={disabled} onClick={copy}>
				<FileCopyOutlinedIcon />
			</IconButton>
		</Tooltip>
	)
}

export default CopyToClipboard
