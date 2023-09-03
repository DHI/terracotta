import React, { FC, Fragment } from 'react'
import { Box, Typography, Link, Tooltip } from '@mui/material'
import { KeyItem } from '../common/data/getData'
import HeaderImage from '../common/images/header.svg'

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
	keys?: KeyItem[]
}
const SidebarTitle: FC<Props> = ({ host, keys }) => (
	<Box sx={styles.wrapper}>
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
				<Typography sx={styles.hostText} variant="body2">
					<b>Host: </b>
					{host}
				</Typography>
				<Typography sx={styles.hostText} variant="body2">
					<b>Docs: </b>
					<Link href={`${host}/apidoc`} target="_blank">
						{`${host}/apidoc`}
					</Link>
				</Typography>
				<Typography
					display="inline-block"
					fontWeight="bold"
					sx={styles.hostText}
					variant="body2"
				>
					Keys:&nbsp;
				</Typography>

				{keys.map((key) => (
					<Fragment key={key.original}>
						<Typography display="inline-block" variant="body2">
							/
						</Typography>
						<Tooltip
							key={`tooltip-${key.original}`}
							title={key.description || false}
						>
							<Typography
								display="inline-block"
								sx={
									key.description ? styles.hasDescription : styles.noDescription
								}
								variant="body2"
							>{`{${key.original}}`}</Typography>
						</Tooltip>
					</Fragment>
				))}
			</Box>
		)}
	</Box>
)

export default SidebarTitle
