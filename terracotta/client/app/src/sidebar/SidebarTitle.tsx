import React, { CSSProperties, FC } from 'react'
import { Box, Typography, Link, Tooltip } from '@material-ui/core'
import HeaderImage from "./../common/images/header.svg"
import { makeStyles } from "@material-ui/core/styles"
import { KeyItem } from "./../common/data/getData"
const useStyles = makeStyles(() => ({
	wrapper: {
		margin: 16,
		backgroundColor: '#FFFFFF',
		borderBottom: '1px solid #86A2B3'
	},
	icon: {
		width: 20,
		height: 22,
		"&:hover":{
			opacity: .7
		}
	},
	infoIcon: {
		marginLeft: 4
	},
	detailsBox: {
		marginTop: 8,
		marginBottom: 8,
		"&:hover":{
			cursor: 'pointer'
		}
	},
	detailsText: {
		marginTop: 6
	},
	hostText: {
		fontSize: 12,
		wordBreak: 'break-all'
	},
	hasDescription: {
		cursor: 'pointer',
		'&:hover': {
			textDecoration: 'underline'
		}
	},
	noDescription: {
		cursor: 'default',
	}
}))

interface Props {
	host?: string,
	style?: CSSProperties,
	details?: string,
	keys?: KeyItem[]
}
const SidebarTitle: FC<Props> = ({
	style,
	host,
	keys
}) => {

	const classes = useStyles()

	return (
		<Box
			style={{ ...style }}
			className={classes.wrapper}
		>
			<Box display={'flex'} flexWrap={'nowrap'} justifyContent={'space-between'} alignItems={'center'}>
				<img src={HeaderImage} alt={'Teracotta preview app'} />
			</Box>
			{
				host && keys && (
					<Box my={1} mt={2}>
						<Typography variant={'body1'} className={classes.hostText}>
							<b>Host: </b>
							<span>
								{host}	
							</span>
						</Typography>
						<Typography variant={'body1'} className={classes.hostText}>
							<b>Docs: </b>
							<Link href={`${host}/apidoc`} target={'_blank'}>
								<span>
									{`${host}/apidoc`}
								</span>
							</Link>
						</Typography>
						<Typography variant={'body1'} className={classes.hostText}>
							<b>{'Keys: '}</b>
							<span>
								{keys.map((keyItem: KeyItem) => 
									keyItem.description ? 
										<Tooltip 
											title={keyItem.description || false}
											key={`tooltip-${keyItem.key}`}
										>
											<span>
												{'/'}
												<span className={classes.hasDescription}>{`{${keyItem.key.toLowerCase()}}`}</span>
											</span>
										</Tooltip>
									:
										<span key={`tooltip-${keyItem.key}`}>
											{'/'}
											<span className={classes.noDescription}>{`{${keyItem.key.toLowerCase()}}`}</span>
										</span>
								)}	
							</span>
						</Typography>
					</Box>
				)
			}
			
		</Box>
	)
}


export default SidebarTitle
