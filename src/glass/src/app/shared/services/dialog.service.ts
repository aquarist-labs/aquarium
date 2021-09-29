import { ComponentType } from '@angular/cdk/portal';
import { Injectable, InjectionToken, Injector } from '@angular/core';
import { NgbModal, NgbModalOptions, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import * as _ from 'lodash';

export const GLASS_DIALOG_DATA: InjectionToken<any> = new InjectionToken<any>('GlassDialogData');

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  constructor(private ngbModal: NgbModal) {}

  open(
    component: ComponentType<any>,
    onClose?: (result: any) => void,
    data?: any,
    options?: NgbModalOptions
  ): NgbModalRef {
    const injector: Injector = Injector.create({
      providers: [{ provide: GLASS_DIALOG_DATA, useValue: data }]
    });
    options = _.defaultTo(options, {});
    _.defaultsDeep(options, { backdrop: 'static', centered: true, injector });
    const modalRef = this.ngbModal.open(component, options);
    if (_.isFunction(onClose)) {
      modalRef.closed.subscribe((result: any) => {
        onClose(result);
      });
    }
    return modalRef;
  }

  dismissAll(): void {
    this.ngbModal.dismissAll();
  }
}
