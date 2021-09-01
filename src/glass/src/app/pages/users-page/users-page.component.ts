import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { finalize } from 'rxjs/operators';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { translate } from '~/app/i18n.helper';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';
import { User, UserService } from '~/app/shared/services/api/user.service';
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

  constructor(private dialogService: DialogService, private userService: UserService) {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'username',
        sortable: true
      },
      {
        name: TEXT('Full Name'),
        prop: 'full_name',
        sortable: true
      },
      {
        name: TEXT('Disabled'),
        prop: 'disabled',
        sortable: true,
        cellTemplateName: 'checkIcon'
      },
      {
        name: '',
        prop: '',
        cellTemplateName: 'actionMenu',
        cellTemplateConfig: this.onActionMenu.bind(this)
      }
    ];
  }

  loadData(): void {
    this.loading = true;
    this.userService.list().subscribe((data) => {
      this.data = data;
      this.loading = this.firstLoadComplete = true;
    });
  }

  onAdd(): void {
    this.dialogService.open(
      DeclarativeFormModalComponent,
      (res: User | boolean) => {
        if (res) {
          this.blockUI.start(translate(TEXT('Please wait, creating user ...')));
          this.userService
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
                required: true
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
                this.userService
                  .update((res as User).username, res as User)
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
        title: TEXT('Delete'),
        callback: (data: DatatableData) => {
          this.dialogService.open(
            DialogComponent,
            (res: boolean) => {
              if (res) {
                this.blockUI.start(translate(TEXT('Please wait, deleting user ...')));
                this.userService
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
}
