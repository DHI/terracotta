import React, { CSSProperties, FC } from 'react'
import { Box, Typography, Link } from '@material-ui/core'
import HeaderImage from "./../common/images/header.svg"
import { makeStyles } from "@material-ui/core/styles"

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
	}
}))

interface Props {
	host?: string,
	style?: CSSProperties,
	details?: string,
	keys?: string[]
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
									{`${host}`}
									<b>{'/apidoc'}</b>
								</span>
							</Link>
						</Typography>
						<Typography variant={'body1'} className={classes.hostText}>
							<b>{'Keys: '}</b>
							<span>
								{`${keys.map((keyItem: string) => `/{${keyItem.toLowerCase()}}`).join('')}`}	
							</span>
						</Typography>
					</Box>
				)
			}
			
		</Box>
	)
}


export default SidebarTitle
