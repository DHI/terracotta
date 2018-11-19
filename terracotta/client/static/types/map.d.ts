export as namespace Terracotta;

export interface IKey {
  key: string;
  description: string;
}

export interface IKeys {
  keys: Array<IKey>;
}

export interface IKeyConstraint {
  key: string;
  value: string;
}

export interface IOptions {
  [key: string]: any;
}

export interface IDataset {
  type: string;
  date: string;
  id: string;
  band: string;
}

export interface IMetadata {
  bounds: Array<number>;
  convex_hull: {
    type: string;
    coordinates: Array<Array<number>>;
  };
  keys: IDataset;
  mean: number;
  metadata: Object;
  nodata: number;
  percentiles: Array<number>;
  range: Array<number>;
  stdev: number;
  valid_percentage: number;
}

export interface IMapError {
  url: string;
  text: string;
}
