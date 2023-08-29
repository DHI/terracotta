import React, { CSSProperties, FC } from 'react'
import { Box, Typography, Link, Tooltip } from '@mui/material'
import HeaderImage from '../common/images/header.png'
import { KeyItem } from '../common/data/getData'

const styles = {
	wrapper: {
		m: 2,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3',
	},
	icon: {
		width: 20,
		height: 22,
		'&:hover': {
			opacity: 0.7,
		},
	},
	infoIcon: {
		ml: 1,
	},
	detailsBox: {
		mt: 1,
		mb: 1,
		'&:hover': {
			cursor: 'pointer',
		},
	},
	detailsText: {
		mt: 1,
	},
	hostText: {
		fontSize: 12,
		wordBreak: 'break-all',
	},
	hasDescription: {
		cursor: 'pointer',
		'&:hover': {
			textDecoration: 'underline',
		},
	},
	noDescription: {
		cursor: 'default',
	},
}

interface Props {
	host?: string
	style?: CSSProperties
	keys?: KeyItem[]
}
const SidebarTitle: FC<Props> = ({ style, host, keys }) => (
	<Box style={{ ...style, ...styles.wrapper }}>
		<Box
			alignItems="center"
			display="flex"
			flexWrap="nowrap"
			justifyContent="space-between"
		>
			<img alt="Teracotta preview app" src={HeaderImage} />
		</Box>
		{host && keys && (
			<Box mt={2} my={1}>
				<Typography sx={styles.hostText} variant="body1">
					<b>Host: </b>
					<span>{host}</span>
				</Typography>
				<Typography sx={styles.hostText} variant="body1">
					<b>Docs: </b>
					<Link href={`${host}/apidoc`} target="_blank">
						<span>{`${host}/apidoc`}</span>
					</Link>
				</Typography>
				<Typography sx={styles.hostText} variant="body1">
					<b>{'Keys: '}</b>
					<span>
						{keys.map((keyItem: KeyItem) =>
							keyItem.description ? (
								<Tooltip
									key={`tooltip-${keyItem.key}`}
									title={keyItem.description || false}
								>
									<Typography>
										/
										<Typography
											sx={styles.hasDescription}
										>{`{${keyItem.key.toLowerCase()}}`}</Typography>
									</Typography>
								</Tooltip>
							) : (
								<Typography key={`tooltip-${keyItem.key}`}>
									/
									<Typography
										sx={styles.noDescription}
									>{`{${keyItem.key.toLowerCase()}}`}</Typography>
								</Typography>
							),
						)}
					</span>
				</Typography>
			</Box>
		)}
	</Box>
)

export default SidebarTitle
