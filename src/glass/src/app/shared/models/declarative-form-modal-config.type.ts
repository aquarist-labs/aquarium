import { DeclarativeFormConfig } from '~/app/shared/models/declarative-form-config.type';

export type DeclarativeFormModalConfig = DeclarativeFormConfig & {
  title: string;
  subtitle?: string;
  okButtonVisible?: boolean; // Defaults to `true`
  okButtonText?: string; // Defaults to `OK`
  okButtonResult?: any; // Defaults to form values
  okButtonClass?: string;
  cancelButtonVisible?: boolean; // Defaults to `true`
  cancelButtonText?: string; // Defaults to `Cancel`
  cancelButtonResult?: any; // Defaults to `false`
  cancelButtonClass?: string;
};
