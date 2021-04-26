import React, { FC, CSSProperties, useContext } from 'react';
import AddIcon from '@material-ui/icons/Add';
import RemoveIcon from '@material-ui/icons/Remove';
import PublicIcon from '@material-ui/icons/Public';
import StreetviewIcon from '@material-ui/icons/Streetview';
import { IconButton, Grid, Tooltip } from '@material-ui/core';
import { makeStyles } from "@material-ui/core/styles"
import AppContext from '../AppContext';
import { Viewport } from "./types"


const useStyles = makeStyles((theme) => ({
  iconButton: {
  	padding: 0
  },
  icon: {
    backgroundColor: '#fff',
    height: 36,
    width: 36,
    fill: '#0B4566',
    padding: 6,
    boxSizing: 'border-box',
    '&:hover': {
      backgroundColor: theme.palette.primary.main,
      fill: '#FFF',
    }
  },
  activeIcon: {
    backgroundColor: '#0b4566',
    '& path': {
      fill: '#fff',
    },
    height: 36,
    width: 36,
    padding: 6,
    boxSizing: 'border-box',
  },
}))

const gridStyle: CSSProperties = {
	position: 'fixed',
	left: 0,
	top: '50%',
	width: 36,
	boxShadow: 'rgba(0, 0, 0, 0.16) 4px 0px 4px',
	zIndex: 100,
	transform: 'translate(0, -50%)',
};

const ZoomControl: FC = () => {
  const classes = useStyles();
  const {
    state: { isOpticalBasemap },
    actions: { setIsOpticalBasemap, setViewport },
  } = useContext(AppContext);

  return (
    <Grid container style={{...gridStyle}}>
      <Grid container>
        <Tooltip placement="right" title={'Change base map'}>
          <IconButton
            onClick={() => setIsOpticalBasemap(!isOpticalBasemap)}
			      className={classes.iconButton}
          >
            {
              !isOpticalBasemap ? <StreetviewIcon className={classes.icon}/> : <PublicIcon className={classes.icon}/>
            }
            {/* <PublicIcon
              className={!isOpticalBasemap ? classes.icon : classes.activeIcon}
            /> */}
          </IconButton>
        </Tooltip>
      </Grid>
      <Grid container>
        <IconButton
          onClick={() => setViewport((v: Viewport) =>({...v, zoom: Number(v.zoom) + 1}))}
		  className={classes.iconButton}
        >
          <AddIcon className={classes.icon} />
        </IconButton>
      </Grid>
      <Grid container>
        <IconButton
          onClick={() => setViewport((v: Viewport) =>({...v, zoom: Number(v.zoom) - 1}))}
		  className={classes.iconButton}
        >
          <RemoveIcon className={classes.icon} />
        </IconButton>
      </Grid>
    </Grid>
  );
};

export default ZoomControl;
