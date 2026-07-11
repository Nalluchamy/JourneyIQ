import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ServerError } from '../pages/ServerError';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught rendering crash caught by ErrorBoundary: ", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return <ServerError />;
    }

    return this.props.children;
  }
}
