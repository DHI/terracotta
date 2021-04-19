import React, { CSSProperties, useState, FC } from 'react'
import { Box, Typography, Paper, Link } from '@material-ui/core'
import HeaderImage from "./../common/images/header.svg"
import ExpandMoreOutlinedIcon from '@material-ui/icons/ExpandMoreOutlined';
import ExpandLessOutlinedIcon from '@material-ui/icons/ExpandLessOutlined';
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined';
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
	details,
	keys
}) => {

	const [ showDetails, setShowDetails ] = useState<boolean>(false)
	const classes = useStyles()

	return (
		<Box
			style={{ ...style }}
			className={classes.wrapper}
		>
			<Box display={'flex'} flexWrap={'nowrap'} justifyContent={'space-between'} alignItems={'center'}>
				<img src={HeaderImage} alt={'Teracotta preview app'} />
			</Box>
			<Paper
				className={classes.detailsBox}
				onClick={() => setShowDetails(!showDetails)}
			>
				<Box 
					display={'flex'}
					justifyContent={'space-between'}
					alignItems={'center'}
				>
					<Box display={'flex'} alignItems={'center'}>
						<Typography variant={'body1'}>
							{'Details'}
						</Typography>
						<InfoOutlinedIcon className={`${classes.icon} ${classes.infoIcon}`}/>
					</Box>
					{ !showDetails ? 
						<ExpandMoreOutlinedIcon className={classes.icon} /> : 
						<ExpandLessOutlinedIcon className={classes.icon} />
					}
				</Box>
				{showDetails && (
					<Typography className={classes.detailsText} variant={'body2'}>
						{details}
					</Typography>
				)}
			</Paper>
			{
				host && keys && (
					<Box my={1}>
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
