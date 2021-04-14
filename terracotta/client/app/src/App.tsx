import React, { FC, useState, useEffect } from 'react';
import { Box } from "@material-ui/core"
import { makeStyles } from "@material-ui/core/styles"
import SidebarControl from "./sidebar/SidebarControl"
import SidebarContent from "./sidebar/SidebarContent"
import SidebarTitle from "./sidebar/SidebarTitle"
import Map from "./map/Map"
import { FlyToInterpolator } from 'react-map-gl'
import { easeCubicInOut } from 'd3-ease'
import AppContext from "./AppContext"
import { Viewport } from "./map/types"
const useStyles = makeStyles(() => ({
  root: {
    width: '100%',
		height: "100vh",
		margin: 0,
		padding: 0,
  }
}))
const details = 'This applet lets you explore the data on any running Terracotta server. Just search for a dataset to get started!'
const defaultViewport = {
  latitude: 10.394947325803054,
	longitude: 8.5887344355014,
	zoom: 5.63,
	bearing: 0,
	pitch: 0,
	transitionDuration: 2000,
	transitionInterpolator: new FlyToInterpolator(),
	transitionEasing: easeCubicInOut,
}

const App: FC = () => {
  const [ isSidebarOpen, setIsSidebarOpen ] = useState<boolean>(true)
  const [ viewport, setViewport ] = useState<Viewport>(defaultViewport)
  const [ isOpticalBasemap, setIsOpticalBasemap ] = useState<boolean>(false)
  const [ hostname, setHostname ] = useState<string | undefined>(undefined)
  const classes = useStyles(); 

	const toggleSidebarOpen = () => setIsSidebarOpen(!isSidebarOpen)

  function initializeApp(hostname: string) {
    // sanitize hostname
    if (hostname.charAt(hostname.length - 1) === '/') {
        hostname = hostname.slice(0, hostname.length - 1);
    }
    setHostname(hostname)
    // STATE.remote_host = hostname;

    // getColormapValues(hostname)
    //     .then(() => getKeys(hostname))
    //     .then((keys) => {
    //         STATE.keys = keys;
    //         initUI(hostname, keys);
    //         updateSearchResults();
    //         let osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    //         let osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';
    //         let osmBase = L.tileLayer(osmUrl, { attribution: osmAttrib });
    //         STATE.map = L.map('map', {
    //             center: [0, 0],
    //             zoom: 2,
    //             layers: [osmBase]
    //         });
    //     });
    // addListenersToSliderRanges();
    // addResizeListeners();
}

  useEffect(() => {
    // window.onload = initializeApp.bind(null, '{{ hostname }}');
    window.onload = initializeApp.bind(null, 'https://4opg6b5hc3.execute-api.eu-central-1.amazonaws.com/development/');
  }, [])

  return (
    <div className={classes.root}>
      <AppContext.Provider value={{
        state: {
          isOpticalBasemap,
          viewport,
          hostname
        },
        actions: {
          setIsOpticalBasemap,
          setViewport,
        }
      }}>
        <Box
          display={'flex'}
          height={1}
          width={1}
        >
          <Map />
          {isSidebarOpen && (
            <SidebarContent>
              <SidebarTitle
                host={hostname}
                details={details}
              />
                <>
                  {/* <EtControl
                    regions={regions}
                    activeRegion={activeRegion}
                    setActiveRegion={(val: number) => setActiveRegion(val)}
                    models={models}
                    activeModel={activeModel}
                    setActiveModel={(val: string) => setActiveModel(val)}
                    ress={ress}
                    activeRes={activeRes}
                    setActiveRes={(val: string) => setActiveRes(val)}
                    products={products}
                    activeProduct={activeProduct}
                    setActiveProduct={(val: string) => setActiveProduct(val)}
                    dates={startingDates}
                    activeDate={activeDate}
                    setActiveDate={(val: string) => setActiveDate(val)}
                  /> */}
                </>
            </SidebarContent>
            )}
            <SidebarControl
              toggleSidebarOpen={toggleSidebarOpen}
              isSidebarOpen={isSidebarOpen}
            />
        </Box>
      </AppContext.Provider>
    </div>
   );
}

export default App;
