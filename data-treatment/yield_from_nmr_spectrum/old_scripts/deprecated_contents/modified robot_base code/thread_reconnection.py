        
    ## This method is modified by Yankai Jia to solve the issue of random thread dropping.
    ## After modification, the threads are reconnected if dropped.
    def _check_command_threads(self):

        """Check that the threads which handle robot command messages are alive.

        Attempt to disconnect from the robot if not.

        """

        if not (self._command_response_handler_thread and self._command_response_handler_thread.is_alive()):
            # raise InvalidStateError('No command response handler thread, are you in monitor mode?')
            self.logger.error('command response handler thread is dropped, relaunching...')
            try:
                self._command_response_handler_thread = self._launch_thread(target=self._command_response_handler,
                                                                            args=())
                time.sleep(1)

                self.logger.error("Command response handler thread relaunched successfully.")

            except Exception as e:
                self.logger.error(f"Failed to restart command response handler thread: {e}")

        if self._offline_mode:  # Do not check rx threads in offline mode.
            return

        if not (self._command_rx_thread and self._command_rx_thread.is_alive()):
            ## if the rx_thread drops, do not raise error and restart it.
            # raise InvalidStateError('No command rx thread, are you in monitor mode?')
            self.logger.error('command rx thread is dropped, relaunching...')
            time.sleep(1)
            try:
                # Restart the rx_thread
                self._command_rx_thread = self._launch_thread(
                    target=self._handle_socket_rx,
                    args=(
                        self._command_socket,
                        self._command_rx_queue,
                        self.logger,
                    )
                )
                time.sleep(1)

                self.logger.error("Command rx thread relaunched successfully.")

            except Exception as e:
                self.logger.error(f"Failed to restart command rx thread: {e}")

        # If tx thread is down, attempt to directly send deactivate command to the robot.
        if not (self._command_tx_thread and self._command_tx_thread.is_alive()):
            ########ORIGINAL###########
            # self._command_socket.sendall(b'DeactivateRobot\0')
            # raise InvalidStateError('No command tx thread, are you in monitor mode?')
            ###########################
            ########By Yankai##########
            self.logger.error('command tx thread is dropped, relaunching...')
            time.sleep(1)
            try:
                self._command_tx_thread = self._launch_thread(target=self._handle_socket_tx,
                                                              args=(
                                                                  self._command_socket,
                                                                  self._command_tx_queue,
                                                                  self.logger,
                                                              ))
                time.sleep(1)

                self.logger.error("Command tx thread relaunched successfully.")

            except Exception as e:
                self.logger.error(f"Failed to restart command tx thread: {e}")

        # print('Command threads are good.')
