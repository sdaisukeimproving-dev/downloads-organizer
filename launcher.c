/*
 * downloads-organizer launcher
 *
 * 役割はひとつだけ。organize.py を「子プロセス」として起動する。
 *
 * なぜこれが必要か:
 *   macOSのフルディスクアクセス許可は「アプリ本体」に紐づく。
 *   シェルスクリプトで exec してpython3に置き換わると、その瞬間に
 *   アプリとしての身元が消え、許可が効かなくなる。
 *   fork + execv で子として起動すれば、親（このバイナリ）が
 *   責任プロセスのまま残り、許可が子に引き継がれる。
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>

#define APPSUP "/Library/Application Support/DownloadsOrganizer"

int main(void) {
    const char *home = getenv("HOME");
    if (!home) return 1;

    char script[2048], config[2048], out[2048];
    snprintf(script, sizeof script, "%s" APPSUP "/organize.py", home);
    snprintf(config, sizeof config, "%s" APPSUP "/rules.json",  home);
    snprintf(out,    sizeof out,    "%s" APPSUP "/run.out",     home);

    pid_t pid = fork();
    if (pid < 0) return 1;
    if (pid == 0) {
        freopen(out, "a", stdout);
        freopen(out, "a", stderr);
        char *const argv[] = { "/usr/bin/python3", script, "--config", config, "--go", NULL };
        execv("/usr/bin/python3", argv);
        _exit(127);
    }
    int st = 0;
    waitpid(pid, &st, 0);
    return WIFEXITED(st) ? WEXITSTATUS(st) : 1;
}
