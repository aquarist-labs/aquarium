/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import * as _ from 'lodash';

/**
 * Convert a binary value into bytes.
 *
 * @param value The value to convert, e.g. '1024', '512MiB' or '2 G'.
 * @returns Returns the value in bytes or NULL in case of an error.
 */
export const toBytes = (value: number | string): number | null => {
  const base = 1024;
  const units = ['b', 'k', 'm', 'g', 't', 'p', 'e', 'z', 'y'];
  const m = RegExp('^(\\d+(.\\d+)?) ?([' + units.join('') + ']?(b|ib|B/s)?)?$', 'i').exec(
    String(value)
  );
  if (_.isNull(m)) {
    return null;
  }
  let bytes = parseFloat(m[1]);
  if (_.isString(m[3])) {
    bytes = bytes * Math.pow(base, units.indexOf(m[3].toLowerCase()[0]));
  }
  return Math.round(bytes);
};

/**
 * Convert a number of bytes into the highest possible binary unit.
 *
 * @param value The value to convert.
 * @returns Returns The converted value, e.g. '4 MiB'.
 */
export const bytesToSize = (value: null | number | string): string => {
  if (_.isNull(value) || [0, '0', ''].includes(value)) {
    return '0 B';
  }
  const bytes = _.toNumber(value);
  const sizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  const factor = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(factor));
  const rawVal = bytes / Math.pow(factor, i);
  const rounded = Math.round((rawVal + Number.EPSILON) * 100) / 100;
  return rounded + ' ' + sizes[i];
};
