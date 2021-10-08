import { Component } from '@angular/core';
import { AbstractControl, AsyncValidatorFn } from '@angular/forms';
import { ValidationErrors } from '@angular/forms';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { Observable, of, timer } from 'rxjs';
import { finalize, map, switchMapTo } from 'rxjs/operators';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { translate } from '~/app/i18n.helper';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';
import { User, UsersService } from '~/app/shared/services/api/users.service';
import { DialogService } from '~/app/shared/services/dialog.service';
@Component({
  selector: 'glass-users-page',
  templateUrl: './users-page.component.html',
  styleUrls: ['./users-page.component.scss']
})
export class UsersPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  loading = false;
  firstLoadComplete = false;
  data: User[] = [];
  columns: DatatableColumn[];

  constructor(private dialogService: DialogService, private usersService: UsersService) {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'username'
      },
      {
        name: TEXT('Full Name'),
        prop: 'full_name'
      },
      {
        name: TEXT('Disabled'),
        prop: 'disabled',
        cellTemplateName: DatatableCellTemplateName.checkIcon
      },
      {
        name: '',
        prop: '',
        unsortable: true,
        cellTemplateName: DatatableCellTemplateName.actionMenu,
        cellTemplateConfig: this.onActionMenu.bind(this)
      }
    ];
  }

  loadData(): void {
    this.loading = true;
    this.usersService
      .list()
      .pipe(
        finalize(() => {
          this.loading = this.firstLoadComplete = true;
        })
      )
      .subscribe((data: User[]) => {
        this.data = data;
      });
  }

  onAdd(): void {
    this.dialogService.open(
      DeclarativeFormModalComponent,
      (res: User | boolean) => {
        if (res) {
          this.blockUI.start(translate(TEXT('Please wait, creating user ...')));
          this.usersService
            .create(res as User)
            .pipe(finalize(() => this.blockUI.stop()))
            .subscribe(() => {
              this.loadData();
            });
        }
      },
      {
        title: TEXT('Add User'),
        formConfig: {
          fields: [
            {
              type: 'text',
              label: TEXT('Name'),
              name: 'username',
              value: '',
              validators: {
                required: true,
                asyncCustom: this.nameValidator()
              }
            },
            {
              type: 'text',
              label: TEXT('Full Name'),
              name: 'full_name',
              value: ''
            },
            {
              type: 'password',
              label: TEXT('Password'),
              name: 'password',
              value: '',
              validators: {
                required: true
              }
            },
            {
              type: 'checkbox',
              label: TEXT('Disabled'),
              name: 'disabled',
              value: false,
              hint: TEXT('Temporarily prohibit the user from logging in.')
            }
          ]
        },
        submitButtonText: TEXT('Add')
      }
    );
  }

  onActionMenu(user: User): DatatableActionItem[] {
    const result: DatatableActionItem[] = [
      {
        title: TEXT('Edit'),
        callback: (data: DatatableData) => {
          this.dialogService.open(
            DeclarativeFormModalComponent,
            (res: User | boolean) => {
              if (res) {
                this.blockUI.start(translate(TEXT('Please wait, updating user ...')));
                this.usersService
                  .update(res as User)
                  .pipe(finalize(() => this.blockUI.stop()))
                  .subscribe(() => {
                    this.loadData();
                  });
              }
            },
            {
              title: TEXT('Edit User'),
              formConfig: {
                fields: [
                  {
                    type: 'text',
                    label: TEXT('Name'),
                    name: 'username',
                    value: user.username,
                    readonly: true
                  },
                  {
                    type: 'text',
                    label: TEXT('Full Name'),
                    name: 'full_name',
                    value: user.full_name
                  },
                  {
                    type: 'password',
                    label: TEXT('Password'),
                    name: 'password',
                    value: ''
                  },
                  {
                    type: 'checkbox',
                    label: TEXT('Disabled'),
                    name: 'disabled',
                    value: user.disabled,
                    hint: TEXT('Temporarily prohibit the user from logging in.')
                  }
                ]
              },
              submitButtonText: TEXT('Edit')
            }
          );
        }
      },
      {
        type: 'divider'
      },
      {
        title: TEXT('Delete'),
        callback: (data: DatatableData) => {
          this.dialogService.open(
            DialogComponent,
            (res: boolean) => {
              if (res) {
                this.blockUI.start(translate(TEXT('Please wait, deleting user ...')));
                this.usersService
                  .delete(data.username)
                  .pipe(finalize(() => this.blockUI.stop()))
                  .subscribe(() => {
                    this.loadData();
                  });
              }
            },
            {
              type: 'yesNo',
              icon: 'question',
              message: TEXT(`Do you really want to delete user <strong>${data.username}</strong>?`)
            }
          );
        }
      }
    ];
    return result;
  }

  private nameValidator(): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      if (control.pristine || _.isEmpty(control.value)) {
        return of(null);
      }
      return timer(200).pipe(
        switchMapTo(this.usersService.exists(control.value)),
        map((resp: boolean) => {
          if (!resp) {
            return null;
          } else {
            return { custom: TEXT('The name is already in use.') };
          }
        })
      );
    };
  }
}
