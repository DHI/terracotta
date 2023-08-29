import { Box, Stack } from '@mui/material'
import React, { FC, useState } from 'react'
import LocalMap from './map/Map'
import SidebarContent from './sidebar/SidebarContent'
import SidebarTitle from './sidebar/SidebarTitle'
import SidebarDatasetsItem from './sidebar-datasets/SidebarDatasets'
import { KeyItem } from './common/data/getData'

interface Props {
	host?: string
	keys?: KeyItem[]
}

const AppScreen: FC<Props> = ({ host, keys }) => {
	const [width, setWidth] = useState((30 / 100) * window.innerWidth)

	return (
		<Stack direction="row" height="100vh" width={1}>
			<LocalMap host={host} width={width} />
			<Stack direction="row" width={width}>
				<SidebarContent setWidth={setWidth} width={width}>
					<SidebarTitle host={host} keys={keys} />
					{host && <SidebarDatasetsItem host={host} />}
				</SidebarContent>
			</Stack>
		</Stack>
	)
}

export default AppScreen
