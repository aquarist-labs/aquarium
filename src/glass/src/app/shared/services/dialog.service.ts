import { ComponentType } from '@angular/cdk/portal';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import * as _ from 'lodash';

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  constructor(private dialog: MatDialog) {}

  open(component: ComponentType<any>, onClose?: (result: any) => void, config?: MatDialogConfig) {
    config = _.defaultTo(config, {});
    _.defaultsDeep(config, { width: '60%' });
    const ref = this.dialog.open(component, config);
    ref.afterClosed().subscribe({
      next: (result) => {
        if (_.isFunction(onClose)) {
          onClose(result);
        }
      }
    });
  }
}
