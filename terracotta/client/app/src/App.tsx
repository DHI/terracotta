import React, { FC, useState, useEffect } from 'react';
import { Box } from "@material-ui/core"
import { makeStyles } from "@material-ui/core/styles"
import SidebarContent from "./sidebar/SidebarContent"
import SidebarTitle from "./sidebar/SidebarTitle"
import SidebarDatasetsItem from "./sidebar-datasets/SidebarDatasets"
import Map from "./map/Map"
import { FlyToInterpolator } from 'react-map-gl'
import { easeCubicInOut } from 'd3-ease'
import AppContext, { activeRGBSelectorRange } from "./AppContext"
import { Viewport } from "./map/types"
import { FeatureDataset } from "./map/types"
import { ResponseMetadata200, KeyItem } from './common/data/getData';
import COLORMAPS, { Colormap } from "./colormap/colormaps"


const useStyles = makeStyles(() => ({
  root: {
    width: '100%',
		height: "100vh",
		margin: 0,
		padding: 0,
  }
}))

const details = 'This applet lets you explore the data on any running Terracotta server. Just search for a dataset to get started!'

const defaultColormap = COLORMAPS[0]

const defaultViewport = {
  latitude: 30.62136584218745,
	longitude: 13.840430671501323,
	zoom: 1,
	bearing: 0,
	pitch: 0,
	transitionDuration: 2000,
	transitionInterpolator: new FlyToInterpolator(),
	transitionEasing: easeCubicInOut,
}

const isEnvDev = process.env.REACT_APP_NODE_ENV === 'development'
const TC_URL = process.env.REACT_APP_TC_URL

export const defaultRGB: activeRGBSelectorRange = {
  R: {
    band: undefined,
    range: undefined
  },
  G: {
    band: undefined,
    range: undefined
  },
  B: {
    band: undefined,
    range: undefined
  },
}

interface Props {
  hostnameProp: string | undefined
}

const App: FC<Props> = ({ hostnameProp }) => {
  const [ viewport, setViewport ] = useState<Viewport>(defaultViewport)
  const [ isOpticalBasemap, setIsOpticalBasemap ] = useState<boolean>(false)

  const [ page, setPage ] = useState<number>(0)
  const [ limit, setLimit ] = useState<number>(15)
  const [ hostname, setHostname ] = useState<string | undefined>(undefined)
  const [ keys, setKeys ] = useState<KeyItem[] | undefined>(undefined)
  const [ datasets, setDatasets ] = useState<ResponseMetadata200[] | undefined>(undefined)
  const [ activeDataset, setActiveDataset ] = useState<number | undefined>(undefined)
  const [ hoveredDataset,  setHoveredDataset ] = useState<FeatureDataset | undefined>(undefined)
  const [ selectedDatasetRasterUrl, setSelectedDatasetRasterUrl ] = useState<string | undefined>(undefined)
  const [ colormap, setColormap ] = useState<Colormap>(defaultColormap)
  const [ activeSinglebandRange, setActiveSinglebandRange ] = useState<[number, number] | undefined>(undefined)
  const [ activeEndpoint, setActiveEndpoint ] = useState<string>('singleband')
  const [ activeRGB, setActiveRGB ] = useState<activeRGBSelectorRange | undefined>(defaultRGB)
  const [ datasetBands, setDatasetBands ] = useState<string[] | undefined>(undefined)

  const classes = useStyles(); 

  const initializeApp = (hostname: string | undefined) => {
    // sanitize hostname

    // when developing, set up your .env in the /app folder with the env. variables:
    // - REACT_APP_NODE_ENV=development
    // - REACT_APP_TC_URL= your TC url to develop with

    if(isEnvDev && TC_URL){
      hostname = TC_URL
    }
    
    if(hostname){

      if (hostname.charAt(hostname.length - 1) === '/') {
          hostname = hostname.slice(0, hostname.length - 1);
      }

      setHostname(hostname)
    
    }
    
}

  useEffect(() => {

    window.onload = initializeApp.bind(null, hostnameProp);

  }, [hostnameProp])

  return (
    <div className={classes.root}>
      <AppContext.Provider value={{
        state: {
          isOpticalBasemap,
          viewport,
          hostname,
          keys,
          hoveredDataset,
          datasets,
          activeDataset,
          selectedDatasetRasterUrl,
          page,
          limit,
          colormap,
          activeSinglebandRange,
          activeEndpoint,
          activeRGB,
          datasetBands
        },
        actions: {
          setIsOpticalBasemap,
          setViewport,
          setKeys,
          setHoveredDataset,
          setDatasets,
          setActiveDataset,
          setSelectedDatasetRasterUrl,
          setPage,
          setLimit,
          setColormap,
          setActiveSinglebandRange,
          setActiveEndpoint,
          setActiveRGB,
          setDatasetBands
        }
      }}>
        <Box
          display={'flex'}
          height={1}
          width={1}
        >
          <Map host={hostname}/>
            <SidebarContent>
              <SidebarTitle
                host={hostname}
                details={details}
                keys={keys}
              />
              {
                hostname && (
                    <SidebarDatasetsItem host={hostname} />
                )
              }
              
            </SidebarContent>
        </Box>
      </AppContext.Provider>
    </div>
   );
}

export default App;
