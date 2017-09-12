package KernelBuilder;

use strict;
use warnings;
use v5.10;

use Scalar::Util "openhandle";

use Exporter "import";
our @EXPORT = qw(merge_kconfig);

sub merge_kconfig {
    my ($main_kconfig_path, $partial_kconfig_path) = @_;

    open(my $main_fh, '+<', $main_kconfig_path) || die "fff";
    open(my $partial_fh, '<', $partial_kconfig_path) || die "die";

    my %config = hashify_conf($partial_fh);
    my @main_content = <$main_fh>;

    @main_content = map {
        if (m/^(?:# )?(?<conf_name>CONFIG_[\w_]*)[\s=](?<status>[ynm]|is\ not\ set)$/
            and exists $config{$+{conf_name}}) {
            my $conf_name = $+{conf_name};
            if ( $config{$conf_name} =~ /[ynm]/ ) {
                my $status = $config{$conf_name};
                delete $config{$conf_name};
                $conf_name . "=" . $status . "\n"
            } else {
                $_
            }
        } else {
            $_
        }
    } @main_content;
    foreach my $conf_opt (keys %config) {
        push @main_content, $conf_opt . "=" . $config{$conf_opt} . "\n"
    }

    seek $main_fh, 0, 0;
    print $main_fh @main_content;

    close($main_fh);
    close($partial_fh);
}

sub hashify_conf {
    my $file = shift;
    my $fh = openhandle($file);
    my $opened_in_sub = undef;
    my %hsh = ();

    if (!$fh) {
        $opened_in_sub = 1;
        open($fh, '<', $file);
        if (!openhandle($file)) {
            exit
        }
    }

    while (<$fh>) {
        m/^(?:#\ )?(?<conf_name>[\w_]*)[\s=](?<status>[ynm]|is\ not\ set)$/;
        $hsh{$+{conf_name}} = $+{status}
    }

    if ($opened_in_sub) {
        close($fh)
    }

    return %hsh;
}

1;
