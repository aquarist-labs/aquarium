import { DatatableData } from '~/app/shared/models/datatable-data.type';

export type DatatableActionItem = {
  title: string;
  callback: (data: DatatableData) => void;
};
