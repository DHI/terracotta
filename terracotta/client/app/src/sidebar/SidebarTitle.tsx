import React, { CSSProperties, ReactNode, FC } from 'react'
import { Box, Typography } from '@material-ui/core'
import HeaderImage from "./../common/images/header.svg"

interface Props {
	title: string,
	titleColor?: string,
	subTitle?: string[],
	subTitleColor?: string,
	images?: ReactNode[],
	imageWidth?: number,
	style?: CSSProperties,
}
const SidebarTitle: FC<Props> = ({
	subTitle = [ '' ],
	subTitleColor = '#86a2b3',
	style,
}) =>

	(
		<Box
			style={{
				padding: 16,
				backgroundColor: '#FFFFFF',
				...style,
			}}
		>
			<Box display={'flex'} flexWrap={'nowrap'} justifyContent={'space-between'} alignItems={'center'}>
				<img src={HeaderImage} alt={'Teracotta preview app'} />
			</Box>
			{(subTitle.length > 0) && (
			<>
				{subTitle.map((text: string, index: number) => (
					<Typography
						key={`subtitle-${index}`}
						style={{ color: subTitleColor }}
						color={'secondary'}
						variant={'subtitle1'}
					>
						{text}
					</Typography>
				))}
			</>
			)}
		</Box>
	)


export default SidebarTitle
